from btclib_node import Node, chains

node = Node(chain=chains.SigNet(), data_dir="test_data", p2p_port=30000, rpc_port=30001)
node.start()
