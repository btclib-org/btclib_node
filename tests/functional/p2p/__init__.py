import time

from btclib_node import Node
from btclib_node.config import Config


def test_init(tmp_path):
    node = Node(
        config=Config(
            chain="regtest", data_dir=tmp_path, allow_p2p=True, allow_rpc=False
        )
    )
    node.start()
    time.sleep(0.1)

    node.stop()
