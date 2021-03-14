from btclib_node.chains import RegTest
from btclib_node.chainstate import Chainstate
from btclib_node.log import Logger
from tests.helpers import generate_random_chain


def test_init(tmp_path):
    Chainstate(tmp_path, Logger(debug=True))


def test_long_init(tmp_path):
    chainstate = Chainstate(tmp_path, Logger(debug=True))
    chain = generate_random_chain(20000, RegTest().genesis.hash)
    for block in chain:
        chainstate.add_block(block)
    chainstate.finalize()
    chainstate.db.close()
    new_chainstate = Chainstate(tmp_path, Logger(debug=True))
    assert chainstate.utxo_dict == new_chainstate.utxo_dict


def test_rev_patch(tmp_path):
    chainstate = Chainstate(tmp_path, Logger(debug=True))
    chain = generate_random_chain(20000, RegTest().genesis.hash)
    rev_patches = []
    for block in chain:
        _, rev_patch = chainstate.add_block(block)
        rev_patches.append(rev_patch)
    rev_patches.reverse()
    for rev_patch in rev_patches:
        chainstate.apply_rev_block(rev_patch)
    chainstate.finalize()
    assert chainstate.utxo_dict == {}
