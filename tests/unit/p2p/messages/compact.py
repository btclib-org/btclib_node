from btclib_node.p2p.messages import get_payload
from btclib_node.p2p.messages.compact import Sendcmpct, Cmptcblock


def test_sendcmpt():
    msg = Sendcmpct(1, 1)
    msg_bytes = bytes.fromhex("00" * 4) + msg.serialize()
    assert msg == Sendcmpct.deserialize(get_payload(msg_bytes)[1])
    msg = Sendcmpct(0, 1)
    msg_bytes = bytes.fromhex("00" * 4) + msg.serialize()
    assert msg == Sendcmpct.deserialize(get_payload(msg_bytes)[1])
