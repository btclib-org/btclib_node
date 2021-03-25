import json

import requests

from btclib_node import Node
from btclib_node.chains import RegTest
from btclib_node.config import Config
from tests.helpers import generate_random_header_chain, get_random_port, wait_until


def test_best_block_hash(tmp_path):
    node = Node(
        config=Config(
            chain="regtest",
            data_dir=tmp_path,
            allow_p2p=False,
            rpc_port=get_random_port(),
        )
    )
    node.start()

    wait_until(lambda: node.rpc_manager.is_alive())

    chain = generate_random_header_chain(2000, RegTest().genesis.hash)
    node.index.add_headers(chain)
    response = json.loads(
        requests.post(
            url=f"http://127.0.0.1:{node.rpc_port}",
            data=json.dumps(
                {
                    "jsonrpc": "1.0",
                    "id": "pytest",
                    "method": "getbestblockhash",
                }
            ).encode(),
            headers={"Content-Type": "text/plain"},
        ).text
    )
    assert response["result"] == chain[-1].hash

    node.stop()


def test_block_hash(tmp_path):
    node = Node(
        config=Config(
            chain="regtest",
            data_dir=tmp_path,
            allow_p2p=False,
            rpc_port=get_random_port(),
        )
    )
    node.start()

    wait_until(lambda: node.rpc_manager.is_alive())

    chain = generate_random_header_chain(2000, RegTest().genesis.hash)
    node.index.add_headers(chain)

    response = json.loads(
        requests.post(
            url=f"http://127.0.0.1:{node.rpc_port}",
            data=json.dumps(
                {
                    "jsonrpc": "1.0",
                    "id": "pytest",
                    "method": "getblockhash",
                    "params": [2000],
                }
            ).encode(),
            headers={"Content-Type": "text/plain"},
        ).text
    )
    assert response["result"] == chain[-1].hash

    node.stop()


def test_block_header_last(tmp_path):
    node = Node(
        config=Config(
            chain="regtest",
            data_dir=tmp_path,
            allow_p2p=False,
            rpc_port=get_random_port(),
        )
    )
    node.start()

    wait_until(lambda: node.rpc_manager.is_alive())

    chain = generate_random_header_chain(2000, RegTest().genesis.hash)
    node.index.add_headers(chain)

    response = json.loads(
        requests.post(
            url=f"http://127.0.0.1:{node.rpc_port}",
            data=json.dumps(
                {
                    "jsonrpc": "1.0",
                    "id": "pytest",
                    "method": "getblockheader",
                    "params": [chain[-1].hash],
                }
            ).encode(),
            headers={"Content-Type": "text/plain"},
        ).text
    )

    assert response["result"]["hash"] == chain[-1].hash
    assert response["result"]["height"] == 2000
    assert response["result"]["previousblockhash"] == chain[-2].hash
    assert "nextblockhash" not in response["result"]

    node.stop()


def test_block_header_middle(tmp_path):
    node = Node(
        config=Config(
            chain="regtest",
            data_dir=tmp_path,
            allow_p2p=False,
            rpc_port=get_random_port(),
        )
    )
    node.start()

    wait_until(lambda: node.rpc_manager.is_alive())

    chain = generate_random_header_chain(2000, RegTest().genesis.hash)
    node.index.add_headers(chain)

    response = json.loads(
        requests.post(
            url=f"http://127.0.0.1:{node.rpc_port}",
            data=json.dumps(
                {
                    "jsonrpc": "1.0",
                    "id": "pytest",
                    "method": "getblockheader",
                    "params": [chain[-1001].hash],
                }
            ).encode(),
            headers={"Content-Type": "text/plain"},
        ).text
    )

    assert response["result"]["hash"] == chain[-1001].hash
    assert response["result"]["height"] == 1000
    assert response["result"]["previousblockhash"] == chain[-1002].hash
    assert response["result"]["nextblockhash"] == chain[-1000].hash

    node.stop()
