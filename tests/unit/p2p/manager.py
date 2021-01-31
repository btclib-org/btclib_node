import asyncio

import pytest

from btclib_node.chains import Main, SigNet, TestNet
from btclib_node.p2p.manager import get_dns_nodes


@pytest.mark.remote_data
def test_main_boostrap_nodes():
    result = asyncio.run(get_dns_nodes(Main()))
    assert len(result)


@pytest.mark.remote_data
def test_testnet_boostrap_nodes():
    result = asyncio.run(get_dns_nodes(TestNet()))
    assert len(result)


@pytest.mark.remote_data
def test_signet_boostrap_nodes():
    result = asyncio.run(get_dns_nodes(SigNet()))
    assert len(result)
