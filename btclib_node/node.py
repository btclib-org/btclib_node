import os
import threading

from btclib_node.chainstate import Chainstate
from btclib_node.index import BlockIndex
from btclib_node.mempool import Mempool
from btclib_node.p2p.main import handle_p2p
from btclib_node.p2p.manager import P2pManager
from btclib_node.rpc.main import handle_rpc
from btclib_node.rpc.manager import RpcManager


class Node(threading.Thread):
    def __init__(self, p2p_port=8333, rpc_port=8334):
        super().__init__()

        self.magic = "f9beb4d9"

        self.index = BlockIndex(
            {}, ["000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8ce26f"]
        )
        self.chainstate = Chainstate({})
        self.mempool = Mempool({})

        self.data_dir = os.path.join(os.getcwd(), "test_data")
        os.makedirs(self.data_dir, exist_ok=True)
        self.lock = threading.Lock()
        self.terminate_flag = threading.Event()

        self.p2p_manager = P2pManager(self, p2p_port)
        self.p2p_manager.start()
        self.rpc_manager = RpcManager(self, rpc_port)
        self.rpc_manager.start()

        self.status = "Syncing"

    def run(self):
        while not self.terminate_flag.is_set():
            if len(self.rpc_manager.messages):
                handle_rpc(self)
            elif len(self.p2p_manager.messages):
                handle_p2p(self)
            pass

    def stop(self):
        self.terminate_flag.set()
        self.p2p_manager.stop()
        self.rpc_manager.stop()

    def connect(self, host, port):
        self.p2p_manager.connect(host, port)
