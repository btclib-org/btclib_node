import random
import socket
import time
from datetime import datetime, timezone

from btclib.exceptions import BTClibValueError
from btclib.hashes import hash256, merkle_root
from btclib.script import script
from btclib.tx.blocks import Block, BlockHeader
from btclib.tx.tx import Tx, TxIn, TxOut
from btclib.tx.tx_in import OutPoint


def generate_random_header_chain(length, start):
    # random.seed(42)
    chain = []
    for x in range(length):
        if chain:
            previous_block_hash = chain[-1].hash
        else:
            previous_block_hash = start
        header = BlockHeader(
            version=70015,
            previous_block_hash=previous_block_hash,
            merkle_root_=random.randrange(256 ** 32).to_bytes(32, "big"),
            time=datetime.fromtimestamp(1231006505 + x + 1, timezone.utc),
            bits=b"\x20\xFF\xFF\xFF",
            nonce=1,
            check_validity=False,
        )
        brute_force_nonce(header)
        chain.append(header)
    return chain


def generate_random_chain(length, start):
    # random.seed(42)
    chain = []
    for x in range(length):
        previous_block_hash = chain[-1].header.hash if chain else start
        coinbase_in = TxIn(
            prev_out=OutPoint(),
            script_sig=script.serialize(
                [random.randrange(256 ** 32).to_bytes(32, "big")]
            ),
            sequence=0xFFFFFFFF,
        )
        coinbase_out = TxOut(
            value=50 * 10 ** 8,
            script_pub_key=script.serialize(
                [random.randrange(256 ** 32).to_bytes(32, "big")]
            ),
        )
        coinbase = Tx(
            version=1,
            lock_time=0,
            vin=[coinbase_in],
            vout=[coinbase_out],
        )
        transactions = [coinbase]
        if chain:
            tx_in = TxIn(
                prev_out=OutPoint(chain[x - 1].transactions[0].id, 0),
                script_sig=script.serialize(
                    [random.randrange(256 ** 32).to_bytes(32, "big")]
                ),
                sequence=0xFFFFFFFF,
            )
            tx_out = TxOut(
                value=50 * 10 ** 8,
                script_pub_key=script.serialize(
                    [random.randrange(256 ** 32).to_bytes(32, "big")]
                ),
            )
            tx = Tx(
                version=1,
                lock_time=0,
                vin=[tx_in],
                vout=[tx_out],
            )
            transactions.append(tx)
        header = BlockHeader(
            version=70015,
            previous_block_hash=previous_block_hash,
            merkle_root_=merkle_root(
                [tx.serialize(True, False) for tx in transactions], hash256
            )[::-1],
            time=datetime.fromtimestamp(1231006505 + x + 1, timezone.utc),
            bits=b"\x20\xFF\xFF\xFF",
            nonce=1,
            check_validity=False,
        )
        brute_force_nonce(header)
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


def wait_until(func, timeout=2):
    start = time.time()
    while time.time() - start < timeout:
        if func():
            return
        time.sleep(0.025)
    raise Exception


def brute_force_nonce(header):
    for _ in range(100):
        try:
            header.assert_valid_pow()
            break
        except BTClibValueError:
            header.nonce += 1
    header.assert_valid()
