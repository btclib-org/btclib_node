import json
import time

import requests

from btclib_node import Node
from btclib_node.config import Config


def test_init(tmp_path):
    node = Node(
        config=Config(
            chain="regtest", data_dir=tmp_path, allow_p2p=False, allow_rpc=True
        )
    )
    node.start()
    time.sleep(0.1)

    response = json.loads(
        requests.post(
            url=f"http://127.0.0.1:{node.rpc_port}",
            data=json.dumps(
                {
                    "jsonrpc": "1.0",
                    "id": "pytest",
                    "method": "stop",
                }
            ).encode(),
            headers={"Content-Type": "text/plain"},
        ).text
    )

    assert response["result"] == "Btclib node stopping"
