import time

from btclib_node import Node
from btclib_node.chains import RegTest


def test_init(tmp_path):
    node = Node(chain=RegTest(), data_dir=tmp_path, p2p_port=30000, rpc_port=30001)
    node.start()
    time.sleep(1)
    node.stop()
