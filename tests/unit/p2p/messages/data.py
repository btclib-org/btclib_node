from btclib import script
from btclib.blocks import Block as BlockData
from btclib.blocks import BlockHeader, _generate_merkle_root
from btclib.tx import Tx as TxData
from btclib.tx import TxIn, TxOut
from btclib.tx_in import OutPoint

from btclib_node.p2p.messages import get_payload
from btclib_node.p2p.messages.data import Block, Blocktxn, Headers, Inv, Tx


def test_tx():
    tx_in = TxIn(
        prevout=OutPoint(),
        scriptSig=script.serialize(["00"]),
        sequence=0xFFFFFFFF,
        txinwitness=[],
    )
    tx_out = TxOut(
        value=50 * 10 ** 8,
        scriptPubKey=script.serialize(["00"]),
    )
    tx = TxData(
        version=1,
        locktime=0,
        vin=[tx_in],
        vout=[tx_out],
    )
    msg = Tx(tx)
    msg_bytes = bytes.fromhex("00" * 4) + msg.serialize()
    assert msg == Tx.deserialize(get_payload(msg_bytes)[1])


def test_block():
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
    header.merkleroot = _generate_merkle_root(transactions)
    msg = Block(BlockData(header, transactions))
    msg_bytes = bytes.fromhex("00" * 4) + msg.serialize()
    assert msg == Block.deserialize(get_payload(msg_bytes)[1])


def test_empty_headers():
    msg = Headers([])
    msg_bytes = bytes.fromhex("00" * 4) + msg.serialize()
    assert msg == Headers.deserialize(get_payload(msg_bytes)[1])


def test_headers():
    headers = []
    for x in range(10):
        headers.append(
            BlockHeader(
                version=70015,
                previousblockhash=f"{x}{x}" * 32,
                merkleroot="00" * 32,
                time=1,
                bits=b"\x23\x00\x00\x01",
                nonce=1,
            )
        )
    msg = Headers(headers)
    msg_bytes = bytes.fromhex("00" * 4) + msg.serialize()
    assert msg == Headers.deserialize(get_payload(msg_bytes)[1])


def test_empty_blocktxn():
    msg = Blocktxn("00" * 32, [])
    msg_bytes = bytes.fromhex("00" * 4) + msg.serialize()
    assert msg == Blocktxn.deserialize(get_payload(msg_bytes)[1])


def test_blocktxn():
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
    msg = Blocktxn("00" * 32, transactions)
    msg_bytes = bytes.fromhex("00" * 4) + msg.serialize()
    assert msg == Blocktxn.deserialize(get_payload(msg_bytes)[1])


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
