from btclib_node.block_db import BlockDB


def test_init(tmp_path):
    BlockDB(tmp_path)
