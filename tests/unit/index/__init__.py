from btclib.blocks import BlockHeader

from btclib_node.chains import Main, RegTest
from btclib_node.index import BlockIndex, BlockInfo, BlockStatus, calculate_work
from tests.helpers import generate_random_header_chain


def test_calculate_work():
    header = BlockHeader(1, "00" * 32, "00" * 32, 1, b"\x23\x00\x00\x01", 1)
    assert calculate_work(header) == 1


def test_empty_init(tmp_path):
    BlockIndex(tmp_path, RegTest())


def test_simple_init(tmp_path):
    index = BlockIndex(tmp_path, RegTest())
    index.add_headers(generate_random_header_chain(2000, RegTest().genesis.hash))
    index.db.close()
    new_index = BlockIndex(tmp_path, RegTest())
    assert index.header_dict == new_index.header_dict
    assert index.header_index == new_index.header_index
    assert index.active_chain == new_index.active_chain
    assert index.block_candidates == new_index.block_candidates


def test_init_with_fork(tmp_path):
    index = BlockIndex(tmp_path, RegTest())
    chain = generate_random_header_chain(2000, RegTest().genesis.hash)
    fork = generate_random_header_chain(5, chain[-10].hash)
    index.add_headers(chain)
    index.add_headers(fork)
    index.db.close()
    new_index = BlockIndex(tmp_path, RegTest())
    assert index.header_dict == new_index.header_dict
    assert index.header_index == new_index.header_index
    assert index.active_chain == new_index.active_chain
    assert sorted(index.block_candidates) == sorted(new_index.block_candidates)


def test_add_headers_fork(tmp_path):
    index = BlockIndex(tmp_path, RegTest())
    chain = generate_random_header_chain(2000, RegTest().genesis.hash)
    fork = generate_random_header_chain(200, chain[-10 - 1].hash)
    index.add_headers(chain)
    index.add_headers(fork)
    assert len(index.header_index) == 2190 + 1


def test_generate_block_candidates(tmp_path):
    index = BlockIndex(tmp_path, RegTest())
    chain = generate_random_header_chain(2000, RegTest().genesis.hash)
    fork = generate_random_header_chain(200, chain[-10 - 1].hash)
    index.add_headers(chain)
    index.add_headers(fork)
    for x in chain:
        block_info = index.get_block_info(x.hash)
        block_info.status = BlockStatus.in_active_chain
        index.insert_block_info(block_info)
    index.db.close()
    new_index = BlockIndex(tmp_path, RegTest())
    assert len(new_index.block_candidates) == 190


def test_generate_block_candidates_2(tmp_path):
    index = BlockIndex(tmp_path, RegTest())
    chain = generate_random_header_chain(2000, RegTest().genesis.hash)
    fork = generate_random_header_chain(200, chain[-10 - 1].hash)
    index.add_headers(chain)
    index.add_headers(fork)
    for x in fork:
        block_info = index.get_block_info(x.hash)
        block_info.status = BlockStatus.invalid
        index.insert_block_info(block_info)
    index.db.close()
    new_index = BlockIndex(tmp_path, RegTest())
    assert len(new_index.block_candidates) == 2000


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
                assert block_info == BlockInfo.deserialize(block_info.serialize())


def test_add_old_header(tmp_path):
    block_index = BlockIndex(tmp_path, RegTest())
    chain = generate_random_header_chain(2000, RegTest().genesis.hash)
    block_index.add_headers(chain)
    assert not block_index.add_headers([chain[10]])
    assert len(block_index.header_dict) == 2000 + 1
    assert len(block_index.header_index) == 2000 + 1
    assert len(block_index.block_candidates) == 2000


def test_add_invalid_header(tmp_path):
    block_index = BlockIndex(tmp_path, RegTest())
    chain = generate_random_header_chain(2000, RegTest().genesis.hash)
    block_index.add_headers(chain)
    invalid_chain = generate_random_header_chain(2000, Main().genesis.hash)
    assert not block_index.add_headers(invalid_chain)
    assert len(block_index.header_dict) == 2000 + 1
    assert len(block_index.header_index) == 2000 + 1
    assert len(block_index.block_candidates) == 2000


def test_add_headers_short(tmp_path):
    block_index = BlockIndex(tmp_path, RegTest())
    length = 10
    chain = generate_random_header_chain(2000 * length, RegTest().genesis.hash)
    for x in range(length):
        block_index.add_headers(chain[x * 2000 : (x + 1) * 2000])
    assert len(block_index.header_dict) == 2000 * length + 1
    assert len(block_index.header_index) == 2000 * length + 1
    assert len(block_index.block_candidates) == 2000 * length


def test_add_headers_medium(tmp_path):
    block_index = BlockIndex(tmp_path, RegTest())
    length = 40  # 400
    chain = generate_random_header_chain(2000 * length, RegTest().genesis.hash)
    for x in range(length):
        block_index.add_headers(chain[x * 2000 : (x + 1) * 2000])
    assert len(block_index.header_dict) == 2000 * length + 1
    assert len(block_index.header_index) == 2000 * length + 1
    assert len(block_index.block_candidates) == 2000 * length


def test_add_headers_long(tmp_path):
    block_index = BlockIndex(tmp_path, RegTest())
    length = 50  # 2000
    chain = generate_random_header_chain(2000 * length, RegTest().genesis.hash)
    for x in range(length):
        block_index.add_headers(chain[x * 2000 : (x + 1) * 2000])
    assert len(block_index.header_dict) == 2000 * length + 1
    assert len(block_index.header_index) == 2000 * length + 1
    assert len(block_index.block_candidates) == 2000 * length


def test_long_init(tmp_path):
    index = BlockIndex(tmp_path, RegTest())
    length = 10  # 2000
    chain = generate_random_header_chain(2000 * length, RegTest().genesis.hash)
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
    chain = generate_random_header_chain(512, RegTest().genesis.hash)
    index.add_headers(chain)
    assert index.get_download_candidates() == [x.hash for x in chain]


def test_block_candidates_2(tmp_path):
    index = BlockIndex(tmp_path, RegTest())
    chain = generate_random_header_chain(1024, RegTest().genesis.hash)
    index.add_headers(chain)
    assert index.get_download_candidates() == [x.hash for x in chain]


def test_block_candidates_3(tmp_path):
    index = BlockIndex(tmp_path, RegTest())
    chain = generate_random_header_chain(2000, RegTest().genesis.hash)
    fork = generate_random_header_chain(200, chain[-10 - 1].hash)
    index.add_headers(chain)
    index.add_headers(fork)
    for x in chain:
        block_info = index.get_block_info(x.hash)
        block_info.status = BlockStatus.in_active_chain
        index.insert_block_info(block_info)
    index.db.close()
    new_index = BlockIndex(tmp_path, RegTest())
    assert new_index.get_download_candidates() == [x.hash for x in fork]


def test_block_locators(tmp_path):
    index = BlockIndex(tmp_path, RegTest())
    chain = generate_random_header_chain(24, RegTest().genesis.hash)
    index.add_headers(chain)
    locators = index.get_block_locator_hashes()
    assert len(locators) == 14


def test_block_locators_2(tmp_path):
    index = BlockIndex(tmp_path, RegTest())
    chain = generate_random_header_chain(2000, RegTest().genesis.hash)
    index.add_headers(chain)
    headers = index.get_headers_from_locators([RegTest().genesis.hash], "00" * 32)
    assert chain == headers


def test_block_locators_3(tmp_path):
    index = BlockIndex(tmp_path, RegTest())
    chain = generate_random_header_chain(2000, RegTest().genesis.hash)
    index.add_headers(chain)
    headers = index.get_headers_from_locators(
        [RegTest().genesis.hash], chain[1000].hash
    )
    assert headers[-1] == chain[1000]
    assert headers == chain[: 1000 + 1]


def test_block_locators_4(tmp_path):
    index = BlockIndex(tmp_path, RegTest())
    chain = generate_random_header_chain(2000, RegTest().genesis.hash)
    index.add_headers(chain[:1000])
    headers = index.get_headers_from_locators(
        [chain[-1].hash, RegTest().genesis.hash], "00" * 32
    )
    assert headers == chain[:1000]
