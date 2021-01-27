import os

from btclib_node import Node
from btclib_node.config import Config


def test_init(tmp_path):
    node1 = Node(
        config=Config(
            chain="regtest",
            data_dir=os.path.join(tmp_path, "node1"),
            p2p_port=60000,
            allow_rpc=False,
        )
    )
    node2 = Node(
        config=Config(
            chain="regtest",
            data_dir=os.path.join(tmp_path, "node2"),
            p2p_port=60001,
            allow_rpc=False,
        )
    )
    node1.start()
    node2.start()
    node2.p2p_manager.connect(("0.0.0.0", 60000))
    while not len(node1.p2p_manager.connections):
        pass
    node1.stop()
    node2.stop()
    node1.join()
    node2.join()
