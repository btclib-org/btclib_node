from btclib_node.p2p.messages import get_payload
from btclib_node.p2p.messages.data import Block, Blocktxn, Headers, Inv, Tx


def test_empty_inv():
    msg = Inv([])
    msg_bytes = bytes.fromhex("00" * 4) + msg.serialize()
    assert msg == Inv.deserialize(get_payload(msg_bytes)[1])


def test_filled_inv():
    msg = Inv([(1, "00" * 32)])
    msg_bytes = bytes.fromhex("00" * 4) + msg.serialize()
    assert msg == Inv.deserialize(get_payload(msg_bytes)[1])


def test_invalid_inv():
    msg = Inv([(1, "00"), (1, "00")])
    msg_bytes = bytes.fromhex("00" * 4) + msg.serialize()
    assert msg != Inv.deserialize(get_payload(msg_bytes)[1])
