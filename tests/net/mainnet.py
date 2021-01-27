from btclib_node import Node
from btclib_node.config import Config

node = Node(
    config=Config(chain="mainnet", data_dir="test_data", p2p_port=30000, rpc_port=30001)
)
node.start()
