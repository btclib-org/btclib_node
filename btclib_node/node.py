import os
import threading
import time
import traceback
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


def block_download(node):
    if node.status == "Synced":

        candidates = node.index.get_download_candidates()
        if not candidates:
            return

        connections = node.p2p_manager.connections.values()
        pending = []
        exit = True
        for conn in connections:
            conn_queue = conn.block_download_queue
            new_queue = []
            for header in conn_queue:
                if not node.index.headers[header].downloaded:
                    new_queue.append(header)
            conn.block_download_queue = new_queue
            pending.extend(new_queue)
            if not new_queue:
                exit = False
        if exit:
            return

        waiting = []
        for header in candidates:
            if header not in pending:
                waiting.append(header)

        node.waiting = waiting
        node.pending = pending

        header_list = waiting + [x[0] for x in Counter(pending).most_common()[::-1]]

        for conn in connections:
            if conn.block_download_queue == []:
                new = header_list[:16]
                header_list = header_list[16:]
                if new:
                    conn.block_download_queue = new
                    conn.send(Getdata([(0x40000002, hash) for hash in new]))
                else:
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
            except Exception:
                traceback.print_exc()

    def stop(self):
        self.terminate_flag.set()
        self.p2p_manager.stop()
        self.rpc_manager.stop()
