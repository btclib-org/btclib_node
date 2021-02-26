import random
import socket

from btclib import script
from btclib.blocks import Block, BlockHeader, _generate_merkle_root
from btclib.tx import Tx, TxIn, TxOut
from btclib.tx_in import OutPoint


def generate_random_header_chain(length, start):
    # random.seed(42)
    chain = []
    for x in range(length):
        if chain:
            previousblockhash = chain[-1].hash
        else:
            previousblockhash = start
        chain.append(
            BlockHeader(
                version=70015,
                previousblockhash=previousblockhash,
                merkleroot=random.randrange(256 ** 32).to_bytes(32, "big").hex(),
                time=1,
                bits=b"\x23\x00\x00\x01",
                nonce=1,
            )
        )
    return chain


def generate_random_chain(length, start):
    # random.seed(42)
    chain = []
    for x in range(length):
        previous_block_hash = chain[-1].header.hash if chain else start
        coinbase_in = TxIn(
            prevout=OutPoint(),
            scriptSig=script.serialize(
                [random.randrange(256 ** 32).to_bytes(32, "big").hex()]
            ),
            sequence=0xFFFFFFFF,
            txinwitness=[],
        )
        coinbase_out = TxOut(
            value=50 * 10 ** 8,
            scriptPubKey=script.serialize(
                [random.randrange(256 ** 32).to_bytes(32, "big").hex()]
            ),
        )
        coinbase = Tx(
            version=1,
            locktime=0,
            vin=[coinbase_in],
            vout=[coinbase_out],
        )
        transactions = [coinbase]
        if chain:
            tx_in = TxIn(
                prevout=OutPoint(chain[x - 1].transactions[0].txid, 0),
                scriptSig=script.serialize(
                    [random.randrange(256 ** 32).to_bytes(32, "big").hex()]
                ),
                sequence=0xFFFFFFFF,
                txinwitness=[],
            )
            tx_out = TxOut(
                value=50 * 10 ** 8,
                scriptPubKey=script.serialize(
                    [random.randrange(256 ** 32).to_bytes(32, "big").hex()]
                ),
            )
            tx = Tx(
                version=1,
                locktime=0,
                vin=[tx_in],
                vout=[tx_out],
            )
            transactions.append(tx)
        header = BlockHeader(
            version=70015,
            previousblockhash=previous_block_hash,
            merkleroot=_generate_merkle_root(transactions),
            time=1,
            bits=b"\x23\x00\x00\x01",
            nonce=1,
        )
        block = Block(header, transactions)
        chain.append(block)
    return chain


def get_random_port():
    while True:
        port = random.randint(1024, 65535)
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(("", port))
            sock.close()
            return port
        except OSError:
            sock.close()
