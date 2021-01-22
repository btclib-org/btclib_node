from btclib_node.chainstate import Chainstate


def test_init(tmp_path):
    Chainstate(tmp_path)
