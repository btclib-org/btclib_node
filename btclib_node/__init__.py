import signal
import threading
import time
from multiprocessing.pool import Pool

from btclib_node.block_db import BlockDB
from btclib_node.chainstate import Chainstate
from btclib_node.config import Config
from btclib_node.constants import NodeStatus
from btclib_node.download import block_download
from btclib_node.index import BlockIndex
from btclib_node.log import Logger
from btclib_node.main import update_chain
from btclib_node.mempool import Mempool
from btclib_node.p2p.address import PeerDB
from btclib_node.p2p.main import handle_p2p, handle_p2p_handshake
from btclib_node.p2p.manager import P2pManager
from btclib_node.rpc.main import handle_rpc
from btclib_node.rpc.manager import RpcManager


class Node(threading.Thread):
    def __init__(self, config=Config()):
        super().__init__()

        def sigint_handler(signal, frame):
            self.stop()

        signal.signal(signal.SIGINT, sigint_handler)

        self.config = config
        self.chain = config.chain
        self.data_dir = config.data_dir
        self.data_dir.mkdir(exist_ok=True, parents=True)

        self.terminate_flag = threading.Event()
        log_path = self.data_dir / config.log_path if config.log_path else None
        self.logger = Logger(log_path, config.debug)

        self.index = BlockIndex(self.data_dir, self.chain, self.logger)
        self.chainstate = Chainstate(self.data_dir, self.logger)
        self.block_db = BlockDB(self.data_dir, self.logger)
        self.mempool = Mempool()

        self.worker_pool = Pool(processes=8)

        self.status = NodeStatus.Starting

        self.download_window = []

        if config.p2p_port:
            self.p2p_port = config.p2p_port
        else:
            self.p2p_port = None
        peer_db = PeerDB(self.chain, self.data_dir)
        self.p2p_manager = P2pManager(self, self.p2p_port, peer_db)

        if config.rpc_port:
            self.rpc_port = config.rpc_port
        else:
            self.rpc_port = None
        self.rpc_manager = RpcManager(self, self.rpc_port)

    def run(self):

        self.logger.info("Starting main loop")

        if self.p2p_port:
            self.p2p_manager.start()
        if self.rpc_port:
            self.rpc_manager.start()
        self.status = NodeStatus.SyncingHeaders
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
                update_chain(self)
            except Exception:
                self.logger.exception("Exception occurred")
                break
        self.p2p_manager.stop()
        self.rpc_manager.stop()

        self.index.close()
        self.chainstate.close()
        self.block_db.close()

        self.worker_pool.terminate()

        self.logger.info("Stopping node")
        self.logger.close()

    def stop(self):
        self.terminate_flag.set()
