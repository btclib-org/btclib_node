from btclib import script
from btclib.blocks import Block as BlockData
from btclib.blocks import BlockHeader, _generate_merkle_root
from btclib.tx import Tx as TxData
from btclib.tx import TxIn, TxOut
from btclib.tx_in import OutPoint

from btclib_node.p2p.messages import get_payload
from btclib_node.p2p.messages.compact import Cmpctblock, Sendcmpct


def test_sendcmpt():
    msg = Sendcmpct(1, 1)
    msg_bytes = bytes.fromhex("00" * 4) + msg.serialize()
    assert msg == Sendcmpct.deserialize(get_payload(msg_bytes)[1])
    msg = Sendcmpct(0, 1)
    msg_bytes = bytes.fromhex("00" * 4) + msg.serialize()
    assert msg == Sendcmpct.deserialize(get_payload(msg_bytes)[1])


def test_cmpctblock():
    transactions = []
    for x in range(10):
        tx_in = TxIn(
            prevout=OutPoint(),
            scriptSig=script.serialize([f"{x}{x}"]),
            sequence=0xFFFFFFFF,
            txinwitness=[],
        )
        tx_out = TxOut(
            value=50 * 10 ** 8,
            scriptPubKey=script.serialize([f"{x}{x}"]),
        )
        tx = TxData(
            version=1,
            locktime=0,
            vin=[tx_in],
            vout=[tx_out],
        )
        transactions.append(tx)
    header = BlockHeader(
        version=1,
        previousblockhash="00" * 32,
        merkleroot="00" * 32,
        time=1,
        bits=b"\x23\x00\x00\x01",
        nonce=1,
    )
    msg = Cmpctblock(
        header,
        1,
        ["00" * 6 for x in range(10)],
        [(x, transactions[x]) for x in range(10)],
    )
    msg_bytes = bytes.fromhex("00" * 4) + msg.serialize()
    assert msg == Cmpctblock.deserialize(get_payload(msg_bytes)[1])
