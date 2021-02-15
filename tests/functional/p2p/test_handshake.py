import time

from btclib_node import Node
from btclib_node.config import Config
from btclib_node.constants import P2pConnStatus
from tests.helpers import get_random_port


def test_simple_connection(tmp_path):
    node1 = Node(
        config=Config(
            chain="regtest",
            data_dir=tmp_path / "node1",
            p2p_port=get_random_port(),
            allow_rpc=False,
        )
    )
    node2 = Node(
        config=Config(
            chain="regtest",
            data_dir=tmp_path / "node2",
            p2p_port=get_random_port(),
            allow_rpc=False,
        )
    )
    node1.start()
    node2.start()
    time.sleep(0.01)  # let them start completely

    node2.p2p_manager.connect(("0.0.0.0", node1.p2p_port))
    while not len(node1.p2p_manager.connections):
        time.sleep(0.001)
    while node1.p2p_manager.connections[0].status != P2pConnStatus.Connected:
        time.sleep(0.001)
    while node2.p2p_manager.connections[0].status != P2pConnStatus.Connected:
        time.sleep(0.001)

    node1.stop()
    node2.stop()


def test_connection_to_ourselves(tmp_path):
    node = Node(
        config=Config(
            chain="regtest",
            data_dir=tmp_path,
            p2p_port=get_random_port(),
            allow_rpc=False,
        )
    )
    node.start()
    time.sleep(0.01)

    node.p2p_manager.connect(("0.0.0.0", node.p2p_port))

    while not len(node.p2p_manager.nonces) == 2:
        time.sleep(0.001)
    while len(node.p2p_manager.connections):
        time.sleep(0.001)
    node.stop()
    return node
