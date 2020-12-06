import os
import threading
import time
from collections import Counter

from btclib_node.chains import Main
from btclib_node.chainstate import Chainstate
from btclib_node.index import BlockIndex
from btclib_node.mempool import Mempool
from btclib_node.p2p.main import handle_p2p
from btclib_node.p2p.manager import P2pManager
from btclib_node.p2p.messages.getdata import Getdata
from btclib_node.rpc.main import handle_rpc
from btclib_node.rpc.manager import RpcManager


def next_to_download(node, waiting, pending):
    if waiting:
        return waiting[:16]
    real_pending = []
    for x in pending:
        if not node.index.headers[x].downloaded:
            real_pending.append(x)
    node.pending = real_pending
    # get the 4 least common headers in pending
    # TODO: must get the 16 which are harder to get, not the 16 least common in pending
    return [x[0] for x in Counter(real_pending).most_common()[:-5:-1]]


def block_download(node):
    if node.status == "Synced":

        connections = node.p2p_manager.connections.values()
        pending = []
        exit = True
        for conn in connections:
            conn_queue = conn.block_download_queue
            if not conn_queue:
                exit = False
            else:
                pending.extend(conn_queue)
        if exit:
            return

        waiting = []
        window_complete = True
        i = node.download_index
        downloadable = node.index.index[i * 1024 : (i + 1) * 1024]
        for header in downloadable:
            if not node.index.headers[header].downloaded:
                if header not in pending:
                    waiting.append(header)
                window_complete = False
        if window_complete:
            node.download_index += 1
            for conn in connections:
                conn.block_download_queue = []
            return

        node.waiting = waiting
        node.pending = pending

        for conn in connections:
            if conn.block_download_queue == []:
                new = next_to_download(node, waiting, pending)
                if new:
                    conn.block_download_queue = new
                    conn.send(Getdata([(0x40000002, hash) for hash in new]))
                return


class Node(threading.Thread):
    def __init__(self, chain=Main(), data_dir=None, p2p_port=None, rpc_port=None):
        super().__init__()

        self.lock = threading.Lock()
        self.terminate_flag = threading.Event()

        self.chain = chain

        if not data_dir:
            data_dir = os.path.join(os.path.expanduser("~"), ".btclib")
        if not os.path.isabs(data_dir):
            self.data_dir = os.path.join(os.getcwd(), data_dir)
        os.makedirs(self.data_dir, exist_ok=True)

        self.index = BlockIndex(data_dir, chain)
        self.chainstate = Chainstate()
        self.mempool = Mempool()

        self.p2p_manager = P2pManager(self, p2p_port if p2p_port else chain.p2p_port)
        self.p2p_manager.start()
        self.rpc_manager = RpcManager(self, rpc_port if rpc_port else chain.rpc_port)
        self.rpc_manager.start()

        self.status = "Syncing"
        self.download_index = 0
        self.waiting = []
        self.pending = []

    def run(self):
        while not self.terminate_flag.is_set():
            if len(self.rpc_manager.messages):
                handle_rpc(self)
            elif len(self.p2p_manager.messages):
                handle_p2p(self)
            else:
                time.sleep(0.0001)
            try:
                block_download(self)
            except Exception as e:
                print(e)
                pass

    def stop(self):
        self.terminate_flag.set()
        self.p2p_manager.stop()
        self.rpc_manager.stop()
