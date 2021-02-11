from btclib_node import Node
from btclib_node.config import Config


def test_init(tmp_path):
    node = Node(
        config=Config(
            chain="regtest", data_dir=tmp_path, allow_p2p=False, allow_rpc=True
        )
    )
    node.start()
    node.stop()
