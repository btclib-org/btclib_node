import time

from btclib_node import Node
from btclib_node.config import Config
from btclib_node.constants import P2pConnStatus
from btclib_node.p2p.messages.ping import Ping
from tests.helpers import get_random_port


def test_correct_ping(tmp_path):
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

    node1.p2p_manager.connections[0].ping_sent = time.time()
    node1.p2p_manager.connections[0].ping_nonce = 1
    node1.p2p_manager.send(Ping(1), 0)

    while not node1.p2p_manager.connections[0].latency:
        time.sleep(0.001)

    node1.stop()
    node2.stop()


def test_wrong_ping(tmp_path):
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

    node1.p2p_manager.connections[0].ping_sent = time.time()
    node1.p2p_manager.connections[0].ping_nonce = 1
    node1.p2p_manager.send(Ping(2), 0)

    while len(node1.p2p_manager.connections):
        time.sleep(0.001)
    while len(node2.p2p_manager.connections):
        time.sleep(0.001)

    node1.stop()
    node2.stop()
