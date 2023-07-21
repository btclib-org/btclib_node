from contextlib import contextmanager

import pytest

from btclib_node import Node
from btclib_node.chains import RegTest
from btclib_node.config import Config
from tests.helpers import get_random_port


@contextmanager
def node_context(tmp_path, allow_p2p: bool = True, allow_rpc: bool = True):
    node = Node(
        config=Config(
            chain="regtest",
            data_dir=tmp_path,
            allow_p2p=allow_p2p,
            p2p_port=get_random_port() if allow_p2p else None,
            allow_rpc=allow_rpc,
            rpc_port=get_random_port() if allow_rpc else None,
            debug=True,
        )
    )
    node.start()
    try:
        yield node
    finally:
        node.stop()


@pytest.fixture()
def rpc_node(tmp_path):
    with node_context(tmp_path, allow_p2p=False) as node:
        yield node
