from btclib_node import chains
from btclib_node.node import Node

node = Node(chain=chains.Main(), data_dir="test_data", p2p_port=30000, rpc_port=30001)
node.start()
