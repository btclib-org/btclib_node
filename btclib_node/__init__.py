import os
import sys
import threading
import time
import traceback

from btclib_node.block_db import BlockDB
from btclib_node.chains import Main
from btclib_node.chainstate import Chainstate
from btclib_node.constants import NodeStatus
from btclib_node.download import block_download
from btclib_node.index import BlockIndex
from btclib_node.main import update_chain
from btclib_node.mempool import Mempool
from btclib_node.p2p.main import handle_p2p, handle_p2p_handshake
from btclib_node.p2p.manager import P2pManager
from btclib_node.rpc.main import handle_rpc
from btclib_node.rpc.manager import RpcManager


class Node(threading.Thread):
    def __init__(self, chain=Main(), data_dir=None, p2p_port=None, rpc_port=None):
        super().__init__()

        self.lock = threading.Lock()
        self.terminate_flag = threading.Event()

        self.chain = chain

        if not data_dir:
            data_dir = os.path.join(os.path.expanduser("~"), ".btclib")
        if not os.path.isabs(data_dir):
            data_dir = os.path.join(os.getcwd(), data_dir)
        self.data_dir = os.path.join(data_dir, chain.name)
        os.makedirs(self.data_dir, exist_ok=True)

        self.index = BlockIndex(self.data_dir, chain)
        self.chainstate = Chainstate(self.data_dir)
        self.block_db = BlockDB(self.data_dir)
        self.mempool = Mempool()

        self.status = NodeStatus.Starting

        self.download_window = []
        self.block_received = False

        self.p2p_manager = P2pManager(self, p2p_port if p2p_port else chain.p2p_port)
        self.p2p_manager.start()
        self.rpc_manager = RpcManager(self, rpc_port if rpc_port else chain.rpc_port)
        self.rpc_manager.start()

        self.status = NodeStatus.SyncingHeaders

    def run(self):
        while not self.terminate_flag.is_set():
            if len(self.p2p_manager.handshake_messages):
                handle_p2p_handshake(self)
            elif len(self.rpc_manager.messages):
                handle_rpc(self)
            elif len(self.p2p_manager.messages):
                handle_p2p(self)
            else:
                time.sleep(0.0001)
            try:
                block_download(self)
                # if self.block_received:
                update_chain(self)
                # self.block_received = False
            except Exception:
                traceback.print_exc()
        self.p2p_manager.stop()
        self.rpc_manager.stop()
        sys.exit(0)

    def stop(self):
        self.terminate_flag.set()
