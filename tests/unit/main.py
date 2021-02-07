from btclib_node import Node
from btclib_node.chains import RegTest
from btclib_node.config import Config
from btclib_node.constants import NodeStatus
from btclib_node.main import update_chain
from tests.helpers import generate_trivial_chain


def test(tmp_path):
    node = Node(
        config=Config(
            chain="regtest", data_dir=tmp_path, allow_p2p=False, allow_rpc=False
        )
    )
    node.status = NodeStatus.HeaderSynced
    length = 1  # 2000
    chain = generate_trivial_chain(2000 * length, RegTest().genesis.hash)
    for x in range(length):
        node.index.add_headers(chain[x * 2000 : (x + 1) * 2000])
    for x in node.index.header_dict.values():
        x.downloaded = True
    for x in range(length * 2000):
        update_chain(node)
    assert len(node.index.active_chain) == 2000 * length + 1
