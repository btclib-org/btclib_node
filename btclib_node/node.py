import os
import threading

from btclib_node.chainstate import Chainstate
from btclib_node.index import BlockIndex
from btclib_node.mempool import Mempool
from btclib_node.p2p.callbacks import callbacks as p2p_callbacks
from btclib_node.p2p.manager import P2pManager


class Node(threading.Thread):
    def __init__(self, p2p_port):
        super().__init__()

        self.magic = "f9beb4d9"

        self.p2p_manager = P2pManager(self, p2p_port)
        self.index = BlockIndex(
            {}, ["000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8ce26f"]
        )
        self.chainstate = Chainstate({})
        self.mempool = Mempool({})

        self.data_dir = os.path.join(os.getcwd(), "test_data")
        os.makedirs(self.data_dir, exist_ok=True)
        self.lock = threading.Lock()
        self.terminate_flag = threading.Event()

        self.p2p_manager.start()

        self.status = "Syncing"

    def run(self):
        callbacks = p2p_callbacks
        while not self.terminate_flag.is_set():
            if len(self.p2p_manager.messages):
                msg_type, msg, conn_id = self.p2p_manager.messages.popleft()
                # print(time.time(), msg_type)
                if msg_type in callbacks:
                    try:
                        conn = self.p2p_manager.connections[conn_id]
                        callbacks[msg_type](self, msg, conn)
                    except Exception as e:
                        print(e)
                        pass

    def stop(self):
        self.terminate_flag.set()
        self.p2p_manager.stop()

    def connect(self, host, port):
        self.p2p_manager.connect(host, port)
