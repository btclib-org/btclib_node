from datetime import datetime, timezone

from btclib.block import BlockHeader

from btclib_node.chains import Main, RegTest
from btclib_node.chainstate import Chainstate
from btclib_node.chainstate.block_index import BlockInfo, BlockStatus, calculate_work
from btclib_node.log import Logger
from tests.helpers import brute_force_nonce, generate_random_header_chain


def test_calculate_work():
    header = BlockHeader(
        1,
        "00" * 32,
        "00" * 32,
        datetime.fromtimestamp(1231006506, timezone.utc),
        b"\x20\xFF\xFF\xFF",
        1,
    )
    brute_force_nonce(header)
    assert calculate_work(header) == 1


def test_simple_init(tmp_path):
    chainstate = Chainstate(tmp_path, RegTest(), Logger(debug=True))
    block_index = chainstate.block_index
    block_index.add_headers(generate_random_header_chain(2000, RegTest().genesis.hash))
    chainstate.db.close()
    new_chainstate = Chainstate(tmp_path, RegTest(), Logger(debug=True))
    new_block_index = new_chainstate.block_index
    assert block_index.header_dict == new_block_index.header_dict
    assert block_index.header_index == new_block_index.header_index
    assert block_index.active_chain == new_block_index.active_chain
    assert block_index.block_candidates == new_block_index.block_candidates


def test_init_with_fork(tmp_path):
    chainstate = Chainstate(tmp_path, RegTest(), Logger(debug=True))
    block_index = chainstate.block_index
    chain = generate_random_header_chain(2000, RegTest().genesis.hash)
    fork = generate_random_header_chain(5, chain[-10].hash)
    block_index.add_headers(chain)
    block_index.add_headers(fork)
    chainstate.db.close()
    new_chainstate = Chainstate(tmp_path, RegTest(), Logger(debug=True))
    new_block_index = new_chainstate.block_index
    assert block_index.header_dict == new_block_index.header_dict
    assert block_index.header_index == new_block_index.header_index
    assert block_index.active_chain == new_block_index.active_chain
    assert sorted(block_index.block_candidates) == sorted(
        new_block_index.block_candidates
    )


def test_add_headers_fork(tmp_path):
    chainstate = Chainstate(tmp_path, RegTest(), Logger(debug=True))
    block_index = chainstate.block_index
    chain = generate_random_header_chain(2000, RegTest().genesis.hash)
    fork = generate_random_header_chain(200, chain[-10 - 1].hash)
    block_index.add_headers(chain)
    block_index.add_headers(fork)
    assert len(block_index.header_index) == 2190 + 1


def test_generate_block_candidates(tmp_path):
    chainstate = Chainstate(tmp_path, RegTest(), Logger(debug=True))
    block_index = chainstate.block_index
    chain = generate_random_header_chain(2000, RegTest().genesis.hash)
    fork = generate_random_header_chain(200, chain[-10 - 1].hash)
    block_index.add_headers(chain)
    block_index.add_headers(fork)
    for x in chain:
        block_info = block_index.get_block_info(x.hash)
        block_info.status = BlockStatus.in_active_chain
        block_index.insert_block_info(block_info)
    chainstate.db.close()
    new_chainstate = Chainstate(tmp_path, RegTest(), Logger(debug=True))
    new_block_index = new_chainstate.block_index
    assert len(new_block_index.block_candidates) == 190


def test_generate_block_candidates_2(tmp_path):
    chainstate = Chainstate(tmp_path, RegTest(), Logger(debug=True))
    block_index = chainstate.block_index
    chain = generate_random_header_chain(2000, RegTest().genesis.hash)
    fork = generate_random_header_chain(200, chain[-10 - 1].hash)
    block_index.add_headers(chain)
    block_index.add_headers(fork)
    for x in fork:
        block_info = block_index.get_block_info(x.hash)
        block_info.status = BlockStatus.invalid
        block_index.insert_block_info(block_info)
    chainstate.db.close()
    new_chainstate = Chainstate(tmp_path, RegTest(), Logger(debug=True))
    new_block_index = new_chainstate.block_index
    assert len(new_block_index.block_candidates) == 2000


def test_block_info_serialization():
    header = BlockHeader(
        1,
        "00" * 32,
        "00" * 32,
        datetime.fromtimestamp(1231006506, timezone.utc),
        b"\x20\xFF\xFF\xFF",
        1,
        check_validity=False,
    )
    brute_force_nonce(header)
    for status in BlockStatus:
        for downloaded in (True, False):
            for x in range(1, 64):
                block_info = BlockInfo(
                    header=header,
                    index=x**2 - 1,
                    status=status,
                    downloaded=downloaded,
                )
                assert block_info == BlockInfo.deserialize(block_info.serialize())


def test_add_old_header(tmp_path):
    chainstate = Chainstate(tmp_path, RegTest(), Logger(debug=True))
    block_index = chainstate.block_index
    chain = generate_random_header_chain(2000, RegTest().genesis.hash)
    block_index.add_headers(chain)
    assert not block_index.add_headers([chain[10]])
    assert len(block_index.header_dict) == 2000 + 1
    assert len(block_index.header_index) == 2000 + 1
    assert len(block_index.block_candidates) == 2000


def test_add_invalid_header(tmp_path):
    chainstate = Chainstate(tmp_path, RegTest(), Logger(debug=True))
    block_index = chainstate.block_index
    chain = generate_random_header_chain(2000, RegTest().genesis.hash)
    block_index.add_headers(chain)
    invalid_chain = generate_random_header_chain(2000, Main().genesis.hash)
    assert not block_index.add_headers(invalid_chain)
    assert len(block_index.header_dict) == 2000 + 1
    assert len(block_index.header_index) == 2000 + 1
    assert len(block_index.block_candidates) == 2000


def test_add_headers_short(tmp_path):
    chainstate = Chainstate(tmp_path, RegTest(), Logger(debug=True))
    block_index = chainstate.block_index
    length = 10
    chain = generate_random_header_chain(2000 * length, RegTest().genesis.hash)
    for x in range(length):
        block_index.add_headers(chain[x * 2000 : (x + 1) * 2000])
    assert len(block_index.header_dict) == 2000 * length + 1
    assert len(block_index.header_index) == 2000 * length + 1
    assert len(block_index.block_candidates) == 2000 * length


def test_add_headers_medium(tmp_path):
    chainstate = Chainstate(tmp_path, RegTest(), Logger(debug=True))
    block_index = chainstate.block_index
    length = 40  # 400
    chain = generate_random_header_chain(2000 * length, RegTest().genesis.hash)
    for x in range(length):
        block_index.add_headers(chain[x * 2000 : (x + 1) * 2000])
    assert len(block_index.header_dict) == 2000 * length + 1
    assert len(block_index.header_index) == 2000 * length + 1
    assert len(block_index.block_candidates) == 2000 * length


def test_add_headers_long(tmp_path):
    chainstate = Chainstate(tmp_path, RegTest(), Logger(debug=True))
    block_index = chainstate.block_index
    length = 50  # 2000
    chain = generate_random_header_chain(2000 * length, RegTest().genesis.hash)
    for x in range(length):
        block_index.add_headers(chain[x * 2000 : (x + 1) * 2000])
    assert len(block_index.header_dict) == 2000 * length + 1
    assert len(block_index.header_index) == 2000 * length + 1
    assert len(block_index.block_candidates) == 2000 * length


def test_long_init(tmp_path):
    chainstate = Chainstate(tmp_path, RegTest(), Logger(debug=True))
    block_index = chainstate.block_index
    length = 50  # 2000
    chain = generate_random_header_chain(2000 * length, RegTest().genesis.hash)
    for x in range(length):
        block_index.add_headers(chain[x * 2000 : (x + 1) * 2000])
    chainstate.db.close()
    new_chainstate = Chainstate(tmp_path, RegTest(), Logger(debug=True))
    new_block_index = new_chainstate.block_index
    assert block_index.header_dict == new_block_index.header_dict
    assert block_index.header_index == new_block_index.header_index
    assert block_index.active_chain == new_block_index.active_chain
    assert block_index.block_candidates == new_block_index.block_candidates


def test_block_candidates(tmp_path):
    chainstate = Chainstate(tmp_path, RegTest(), Logger(debug=True))
    block_index = chainstate.block_index
    chain = generate_random_header_chain(512, RegTest().genesis.hash)
    block_index.add_headers(chain)
    assert block_index.get_download_candidates() == [x.hash for x in chain]


def test_block_candidates_2(tmp_path):
    chainstate = Chainstate(tmp_path, RegTest(), Logger(debug=True))
    block_index = chainstate.block_index
    chain = generate_random_header_chain(1024, RegTest().genesis.hash)
    block_index.add_headers(chain)
    assert block_index.get_download_candidates() == [x.hash for x in chain]


def test_block_candidates_3(tmp_path):
    chainstate = Chainstate(tmp_path, RegTest(), Logger(debug=True))
    block_index = chainstate.block_index
    chain = generate_random_header_chain(2000, RegTest().genesis.hash)
    fork = generate_random_header_chain(200, chain[-10 - 1].hash)
    block_index.add_headers(chain)
    block_index.add_headers(fork)
    for x in chain:
        block_info = block_index.get_block_info(x.hash)
        block_info.status = BlockStatus.in_active_chain
        block_index.insert_block_info(block_info)
    chainstate.db.close()
    new_chainstate = Chainstate(tmp_path, RegTest(), Logger(debug=True))
    new_block_index = new_chainstate.block_index
    assert new_block_index.get_download_candidates() == [x.hash for x in fork]


def test_block_locators(tmp_path):
    chainstate = Chainstate(tmp_path, RegTest(), Logger(debug=True))
    block_index = chainstate.block_index
    chain = generate_random_header_chain(24, RegTest().genesis.hash)
    block_index.add_headers(chain)
    locators = block_index.get_block_locator_hashes()
    assert len(locators) == 14


def test_block_locators_2(tmp_path):
    chainstate = Chainstate(tmp_path, RegTest(), Logger(debug=True))
    block_index = chainstate.block_index
    chain = generate_random_header_chain(2000, RegTest().genesis.hash)
    block_index.add_headers(chain)
    headers = block_index.get_headers_from_locators([RegTest().genesis.hash], "00" * 32)
    assert chain == headers


def test_block_locators_3(tmp_path):
    chainstate = Chainstate(tmp_path, RegTest(), Logger(debug=True))
    block_index = chainstate.block_index
    chain = generate_random_header_chain(2000, RegTest().genesis.hash)
    block_index.add_headers(chain)
    headers = block_index.get_headers_from_locators(
        [RegTest().genesis.hash], chain[1000].hash
    )
    assert headers[-1] == chain[1000]
    assert headers == chain[: 1000 + 1]


def test_block_locators_4(tmp_path):
    chainstate = Chainstate(tmp_path, RegTest(), Logger(debug=True))
    block_index = chainstate.block_index
    chain = generate_random_header_chain(2000, RegTest().genesis.hash)
    block_index.add_headers(chain[:1000])
    headers = block_index.get_headers_from_locators(
        [chain[-1].hash, RegTest().genesis.hash], "00" * 32
    )
    assert headers == chain[:1000]
