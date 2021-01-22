from btclib_node.mempool import Mempool


def test_init(tmp_path):
    Mempool(tmp_path)
