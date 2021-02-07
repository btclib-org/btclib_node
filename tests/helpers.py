import random

from btclib.blocks import BlockHeader


def generate_trivial_chain(length, start):
    random.seed(42)
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
