from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List

from btclib.hashes import hash256, merkle_root
from btclib.script import script
from btclib.tx.blocks import BlockHeader
from btclib.tx.tx import Tx
from btclib.tx.tx_in import OutPoint, TxIn
from btclib.tx.tx_out import TxOut


def create_genesis(time, nonce, difficulty, version, reward):
    script_sig = script.serialize(
        [
            "FFFF001D",
            b"\x04",
            "The Times 03/Jan/2009 Chancellor on brink of second bailout for banks".encode(),
        ]
    )
    script_pub_key = script.serialize(
        [
            "04678afdb0fe5548271967f1a67130b7105cd6a828e03909a67962e0ea1f61deb649f6bc3f4cef38c4f35504e51ec112de5c384df7ba0b8d578a4c702b6bf11d5f",
            "OP_CHECKSIG",
        ]
    )
    tx_in = TxIn(
        prev_out=OutPoint(),
        script_sig=script_sig,
        sequence=0xFFFFFFFF,
    )
    tx_out = TxOut(
        value=reward,
        script_pub_key=script_pub_key,
    )
    tx = Tx(
        version=1,
        lock_time=0,
        vin=[tx_in],
        vout=[tx_out],
    )
    header = BlockHeader(
        version=version,
        previous_block_hash="00" * 32,
        merkle_root_="00" * 32,
        time=datetime.fromtimestamp(time, timezone.utc),
        bits=difficulty.to_bytes(4, "big"),
        nonce=nonce,
        check_validity=False,
    )
    header.merkle_root = merkle_root([tx.serialize(False)], hash256)[::-1]
    header.assert_valid()
    return header


@dataclass
class Chain:
    name: str
    port: int
    magic: str
    addresses: List[str]
    genesis: BlockHeader


@dataclass
class Main(Chain):
    def __init__(self):
        self.name = "mainnet"
        self.port = 8333
        self.magic = "f9beb4d9"
        self.addresses = [
            "seed.bitcoin.sipa.be",
            "dnsseed.bluematt.me",
            "dnsseed.bitcoin.dashjr.org",
            "seed.bitcoinstats.com",
            "seed.bitcoin.jonasschnelli.ch",
            "seed.btc.petertodd.org",
            "seed.bitcoin.sprovoost.nl",
            "dnsseed.emzy.de",
            "seed.bitcoin.wiz.biz",
        ]
        self.genesis = create_genesis(
            1231006505, 2083236893, 0x1D00FFFF, 1, 50 * 10 ** 8
        )


@dataclass
class TestNet(Chain):
    def __init__(self):
        self.name = "testnet"
        self.port = 18333
        self.magic = "0b110907"
        self.addresses = [
            "testnet-seed.bitcoin.jonasschnelli.ch",
            "seed.tbtc.petertodd.org",
            "seed.testnet.bitcoin.sprovoost.nl",
            "testnet-seed.bluematt.me",
        ]
        self.genesis = create_genesis(
            1296688602, 414098458, 0x1D00FFFF, 1, 50 * 10 ** 8
        )


@dataclass
class SigNet(Chain):
    def __init__(self):
        self.name = "signet"
        self.port = 38333
        self.magic = "0a03cf40"  # default signet
        self.addresses = ["178.128.221.177"]
        self.genesis = create_genesis(1598918400, 52613770, 0x1E0377AE, 1, 50 * 10 ** 8)


@dataclass
class RegTest(Chain):
    def __init__(self):
        self.name = "regtest"
        self.port = 18444
        self.magic = "fabfb5da"
        self.addresses = []
        self.genesis = create_genesis(1296688602, 2, 0x207FFFFF, 1, 50 * 10 ** 8)
