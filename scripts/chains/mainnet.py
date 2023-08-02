from btclib_node import Node
from btclib_node.config import Config

node = Node(
    config=Config(
        chain="mainnet",
        data_dir=".btclib",
        p2p_port=30000,
        rpc_port=30001,
        debug=True,
        log_path=None,
    )
)
node.start()
