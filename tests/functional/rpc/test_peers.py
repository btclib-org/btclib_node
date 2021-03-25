import json

import requests

from btclib_node import Node
from btclib_node.config import Config
from btclib_node.constants import P2pConnStatus
from tests.helpers import get_random_port, wait_until


def test_get_connection_count(tmp_path):
    node1 = Node(
        config=Config(
            chain="regtest",
            data_dir=tmp_path / "node1",
            p2p_port=get_random_port(),
            rpc_port=get_random_port(),
        )
    )
    node2 = Node(
        config=Config(
            chain="regtest",
            data_dir=tmp_path / "node2",
            p2p_port=get_random_port(),
            rpc_port=get_random_port(),
        )
    )
    node1.start()
    node2.start()

    wait_until(lambda: node1.rpc_manager.is_alive())
    wait_until(lambda: node2.rpc_manager.is_alive())

    node2.p2p_manager.connect(("0.0.0.0", node1.p2p_port))
    wait_until(lambda: len(node1.p2p_manager.connections))
    connection = node1.p2p_manager.connections[0]
    wait_until(lambda: connection.status == P2pConnStatus.Connected)
    connection = node2.p2p_manager.connections[0]
    wait_until(lambda: connection.status == P2pConnStatus.Connected)

    response = json.loads(
        requests.post(
            url=f"http://127.0.0.1:{node1.rpc_port}",
            data=json.dumps(
                {
                    "jsonrpc": "1.0",
                    "id": "pytest",
                    "method": "getconnectioncount",
                }
            ).encode(),
            headers={"Content-Type": "text/plain"},
        ).text
    )

    assert response["result"] == 1

    node1.stop()
    node2.stop()


def test_get_peer_info(tmp_path):
    node1 = Node(
        config=Config(
            chain="regtest",
            data_dir=tmp_path / "node1",
            p2p_port=get_random_port(),
            rpc_port=get_random_port(),
        )
    )
    node2 = Node(
        config=Config(
            chain="regtest",
            data_dir=tmp_path / "node2",
            p2p_port=get_random_port(),
            rpc_port=get_random_port(),
        )
    )
    node1.start()
    node2.start()

    wait_until(lambda: node1.rpc_manager.is_alive())
    wait_until(lambda: node2.rpc_manager.is_alive())

    node2.p2p_manager.connect(("0.0.0.0", node1.p2p_port))
    wait_until(lambda: len(node1.p2p_manager.connections))
    connection = node1.p2p_manager.connections[0]
    wait_until(lambda: connection.status == P2pConnStatus.Connected)
    connection = node2.p2p_manager.connections[0]
    wait_until(lambda: connection.status == P2pConnStatus.Connected)

    local_port = node1.p2p_manager.connections[0].client.getpeername()[1]

    response = json.loads(
        requests.post(
            url=f"http://127.0.0.1:{node2.rpc_port}",
            data=json.dumps(
                {
                    "jsonrpc": "1.0",
                    "id": "pytest",
                    "method": "getpeerinfo",
                }
            ).encode(),
            headers={"Content-Type": "text/plain"},
        ).text
    )
    assert response["result"][0]["id"] == 0
    assert response["result"][0]["addr"] == f"127.0.0.1:{node1.p2p_port}"
    assert response["result"][0]["addrbind"] == f"127.0.0.1:{local_port}"
    assert response["result"][0]["addrlocal"] == f"127.0.0.1:{local_port}"

    response = json.loads(
        requests.post(
            url=f"http://127.0.0.1:{node1.rpc_port}",
            data=json.dumps(
                {
                    "jsonrpc": "1.0",
                    "id": "pytest",
                    "method": "getpeerinfo",
                }
            ).encode(),
            headers={"Content-Type": "text/plain"},
        ).text
    )
    assert response["result"][0]["id"] == 0
    assert response["result"][0]["addr"] == f"127.0.0.1:{local_port}"
    assert response["result"][0]["addrbind"] == f"127.0.0.1:{node1.p2p_port}"
    assert response["result"][0]["addrlocal"] == f"127.0.0.1:{node1.p2p_port}"

    node1.stop()
    node2.stop()
