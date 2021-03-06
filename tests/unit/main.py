from btclib_node import Node
from btclib_node.chains import RegTest
from btclib_node.config import Config
from btclib_node.constants import NodeStatus
from btclib_node.main import update_chain
from tests.helpers import generate_random_chain


def test(tmp_path):
    node = Node(
        config=Config(
            chain="regtest", data_dir=tmp_path, allow_p2p=False, allow_rpc=False
        )
    )
    node.status = NodeStatus.HeaderSynced
    length = 2000 * 1  # 2000
    chain = generate_random_chain(length, RegTest().genesis.hash)
    headers = [block.header for block in chain]
    for x in range(0, length, 2000):
        node.index.add_headers(headers[x : x + 2000])
    for x in node.index.header_dict:
        block_info = node.index.get_block_info(x)
        block_info.downloaded = True
        node.index.insert_block_info(block_info)
    for block in chain:
        node.block_db.add_block(block)
    for x in range(len(chain)):
        update_chain(node)
    assert len(node.index.active_chain) == length + 1
