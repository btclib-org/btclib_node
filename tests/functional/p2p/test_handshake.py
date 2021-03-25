from btclib_node import Node
from btclib_node.config import Config
from btclib_node.constants import P2pConnStatus
from tests.helpers import get_random_port, wait_until


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

    wait_until(lambda: node1.p2p_manager.is_alive())
    wait_until(lambda: node2.p2p_manager.is_alive())

    node2.p2p_manager.connect(("0.0.0.0", node1.p2p_port))
    wait_until(lambda: len(node1.p2p_manager.connections))
    connection = node1.p2p_manager.connections[0]
    wait_until(lambda: connection.status == P2pConnStatus.Connected)
    connection = node2.p2p_manager.connections[0]
    wait_until(lambda: connection.status == P2pConnStatus.Connected)

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

    wait_until(lambda: node.p2p_manager.is_alive())

    node.p2p_manager.connect(("0.0.0.0", node.p2p_port))

    wait_until(lambda: len(node.p2p_manager.nonces) == 2)
    wait_until(lambda: not len(node.p2p_manager.connections))

    node.stop()
