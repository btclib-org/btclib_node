from btclib_node.chains import RegTest
from btclib_node.chainstate import Chainstate
from btclib_node.log import Logger


def test_init(tmp_path):
    Chainstate(tmp_path, RegTest(), Logger(debug=True))
