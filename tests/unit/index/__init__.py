from btclib.blocks import BlockHeader

from btclib_node.chains import RegTest
from btclib_node.index import BlockIndex, BlockInfo, BlockStatus


def test_init(tmp_path):
    BlockIndex(tmp_path, RegTest())


def test_block_info_serialization():
    header = BlockHeader(1, "00" * 32, "00" * 32, 1, b"\xff\xff\xff\xff", 1)
    for status in BlockStatus:
        for downloaded in (True, False):
            for x in range(1, 64):
                block_info = BlockInfo(
                    header=header,
                    index=x ** 2 - 1,
                    status=status,
                    downloaded=downloaded,
                )
                assert block_info == BlockInfo.deserialize(block_info.serialize())
