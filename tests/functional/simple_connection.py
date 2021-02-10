import time

from btclib_node import Node
from btclib_node.config import Config
from btclib_node.constants import P2pConnStatus


def test_simple_connection(tmp_path):
    node1 = Node(
        config=Config(
            chain="regtest",
            data_dir=tmp_path / "node1",
            p2p_port=60000,
            allow_rpc=False,
        )
    )
    node2 = Node(
        config=Config(
            chain="regtest",
            data_dir=tmp_path / "node2",
            p2p_port=60001,
            allow_rpc=False,
        )
    )
    node1.start()
    node2.start()
    node2.p2p_manager.connect(("0.0.0.0", 60000))

    while not len(node1.p2p_manager.connections):
        time.sleep(0.01)
    while node1.p2p_manager.connections[0].status != P2pConnStatus.Connected:
        time.sleep(0.01)

    assert node1.p2p_manager.connections[0].status == P2pConnStatus.Connected
    assert node2.p2p_manager.connections[0].status == P2pConnStatus.Connected
    node1.stop()
    node2.stop()
