from ipaddress import IPv6Address

from btclib_node.p2p.address import NetworkAddress
from btclib_node.p2p.messages import get_payload
from btclib_node.p2p.messages.address import Addr, Getaddr


def test_empty_addr():
    msg = Addr([])
    msg_bytes = bytes.fromhex("00" * 4) + msg.serialize()
    assert msg == Addr.deserialize(get_payload(msg_bytes)[1])


def test_valid_addr():
    msg = Addr([(1, NetworkAddress(0, IPv6Address(1), 1))])
    msg_bytes = bytes.fromhex("00" * 4) + msg.serialize()
    assert msg == Addr.deserialize(get_payload(msg_bytes)[1])


def test_valid_getaddr():
    msg = Getaddr()
    msg_bytes = bytes.fromhex("00" * 4) + msg.serialize()
    assert msg == Getaddr.deserialize(get_payload(msg_bytes)[1])
