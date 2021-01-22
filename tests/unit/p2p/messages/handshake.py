from btclib_node.p2p.messages import get_payload
from btclib_node.p2p.messages.handshake import Version, Verack


def test_verack():
    msg = Verack()
    msg_bytes = bytes.fromhex("00" * 4) + msg.serialize()
    assert msg == Verack.deserialize(get_payload(msg_bytes)[1])
