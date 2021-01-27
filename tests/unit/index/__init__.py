from btclib.blocks import BlockHeader

from btclib_node.chains import RegTest
from btclib_node.index import BlockIndex, BlockInfo, BlockStatus


def generate_trivial_chain(length, start):
    chain = []
    for x in range(length):
        if chain:
            previousblockhash = chain[-1].hash
        else:
            previousblockhash = start
        chain.append(
            BlockHeader(
                version=70015,
                previousblockhash=previousblockhash,
                merkleroot="00" * 32,
                time=1,
                bits=b"\x23\x00\x00\x01",
                nonce=1,
            )
        )
    return chain


def test_empty_init(tmp_path):
    BlockIndex(tmp_path, RegTest())


def test_init(tmp_path):
    index = BlockIndex(tmp_path, RegTest())
    index.add_headers(generate_trivial_chain(2000, RegTest().genesis.hash))
    index.db.close()
    new_index = BlockIndex(tmp_path, RegTest())
    assert index.header_dict == new_index.header_dict
    assert index.header_index == new_index.header_index
    assert index.active_chain == new_index.active_chain
    assert index.block_candidates == new_index.block_candidates


def test_block_info_serialization():
    header = BlockHeader(1, "00" * 32, "00" * 32, 1, b"\x23\x00\x00\x01", 1)
    for status in BlockStatus:
        for downloaded in (True, False):
            for x in range(1, 64):
                block_info = BlockInfo(
                    header=header,
                    index=x ** 2 - 1,
                    status=status,
                    downloaded=downloaded,
                )
                assert block_info.work == 1
                assert block_info == BlockInfo.deserialize(block_info.serialize())


def test_add_headers_short(tmp_path):
    block_index = BlockIndex(tmp_path, RegTest())
    length = 10
    chain = generate_trivial_chain(2000 * length, RegTest().genesis.hash)
    for x in range(length):
        block_index.add_headers(chain[x * 2000 : (x + 1) * 2000])
    assert len(block_index.header_dict) == 2000 * length + 1


def test_add_headers_medium(tmp_path):
    block_index = BlockIndex(tmp_path, RegTest())
    length = 40  # 400
    chain = generate_trivial_chain(2000 * length, RegTest().genesis.hash)
    for x in range(length):
        block_index.add_headers(chain[x * 2000 : (x + 1) * 2000])
    assert len(block_index.header_dict) == 2000 * length + 1


def test_add_headers_long(tmp_path):
    block_index = BlockIndex(tmp_path, RegTest())
    length = 50  # 2000
    chain = generate_trivial_chain(2000 * length, RegTest().genesis.hash)
    for x in range(length):
        block_index.add_headers(chain[x * 2000 : (x + 1) * 2000])
    assert len(block_index.header_dict) == 2000 * length + 1


def test_long_init(tmp_path):
    index = BlockIndex(tmp_path, RegTest())
    length = 10  # 2000
    chain = generate_trivial_chain(2000 * length, RegTest().genesis.hash)
    for x in range(length):
        index.add_headers(chain[x * 2000 : (x + 1) * 2000])
    index.db.close()
    new_index = BlockIndex(tmp_path, RegTest())
    assert index.header_dict == new_index.header_dict
    assert index.header_index == new_index.header_index
    assert index.active_chain == new_index.active_chain
    assert index.block_candidates == new_index.block_candidates


def test_block_candidates(tmp_path):
    index = BlockIndex(tmp_path, RegTest())
    chain = generate_trivial_chain(1024, RegTest().genesis.hash)
    index.add_headers(chain)
    assert index.get_download_candidates() == [x.hash for x in chain]


def test_block_locators(tmp_path):
    index = BlockIndex(tmp_path, RegTest())
    chain = generate_trivial_chain(24, RegTest().genesis.hash)
    index.add_headers(chain)
    locators = index.get_block_locator_hashes()
    assert len(locators) == 14


def test_block_locators_2(tmp_path):
    index = BlockIndex(tmp_path, RegTest())
    chain = generate_trivial_chain(2000, RegTest().genesis.hash)
    index.add_headers(chain)
    headers = index.get_headers_from_locators([RegTest().genesis.hash], "00" * 32)
    assert chain == headers
