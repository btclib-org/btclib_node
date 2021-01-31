from btclib_node.p2p.messages import get_payload
from btclib_node.p2p.messages.getdata import (
    Getblocks,
    Getblocktxn,
    Getdata,
    Getheaders,
    Mempool,
    Sendheaders,
)


def test_sendheaders():
    msg = Sendheaders()
    msg_bytes = bytes.fromhex("00" * 4) + msg.serialize()
    assert msg == Sendheaders.deserialize(get_payload(msg_bytes)[1])


def test_mempool():
    msg = Mempool()
    msg_bytes = bytes.fromhex("00" * 4) + msg.serialize()
    assert msg == Mempool.deserialize(get_payload(msg_bytes)[1])


def test_getdata():
    msg = Getdata([(1, "00" * 32)])
    msg_bytes = bytes.fromhex("00" * 4) + msg.serialize()
    assert msg == Getdata.deserialize(get_payload(msg_bytes)[1])


def test_getblocks():
    msg = Getblocks(70015, ["00" * 32, "11" * 32], "00" * 32)
    msg_bytes = bytes.fromhex("00" * 4) + msg.serialize()
    assert msg == Getblocks.deserialize(get_payload(msg_bytes)[1])


def test_getheaders():
    msg = Getheaders(70015, ["00" * 32, "11" * 32], "00" * 32)
    msg_bytes = bytes.fromhex("00" * 4) + msg.serialize()
    assert msg == Getheaders.deserialize(get_payload(msg_bytes)[1])


def test_getblocktxn():
    msg = Getblocktxn("00" * 32, [2 ** x for x in range(10)])
    msg_bytes = bytes.fromhex("00" * 4) + msg.serialize()
    assert msg == Getblocktxn.deserialize(get_payload(msg_bytes)[1])
