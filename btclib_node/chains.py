from btclib import script
from btclib.blocks import BlockHeader, _generate_merkle_root
from btclib.tx import Tx
from btclib.tx_in import OutPoint, TxIn
from btclib.tx_out import TxOut


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
        prevout=OutPoint(),
        scriptSig=script_sig,
        sequence=0xFFFFFFFF,
        txinwitness=[],
    )
    tx_out = TxOut(
        value=reward,
        scriptPubKey=script_pub_key,
    )
    tx = Tx(
        version=1,
        locktime=0,
        vin=[tx_in],
        vout=[tx_out],
    )
    header = BlockHeader(
        version=version,
        previousblockhash="00" * 32,
        merkleroot="00" * 32,
        time=time,
        bits=difficulty.to_bytes(4, "big"),
        nonce=nonce,
    )
    header.merkleroot = _generate_merkle_root([tx])
    return header


class Main:
    name = "mainnet"
    p2p_port = 8333
    rpc_port = 8334
    magic = "f9beb4d9"
    addresses = [
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
    genesis = create_genesis(1231006505, 2083236893, 0x1D00FFFF, 1, 50 * 10 ** 8)


class TestNet:
    name = "testnet"
    p2p_port = 18333
    rpc_port = 18334
    magic = "0b110907"
    addresses = [
        "testnet-seed.bitcoin.jonasschnelli.ch",
        "seed.tbtc.petertodd.org",
        "seed.testnet.bitcoin.sprovoost.nl",
        "testnet-seed.bluematt.me",
    ]
    genesis = create_genesis(1296688602, 414098458, 0x1D00FFFF, 1, 50 * 10 ** 8)


class SigNet:
    name = "signet"
    p2p_port = 38333
    rpc_port = 38334
    magic = "0a03cf40"  # default signet
    addresses = ["178.128.221.177"]
    genesis = create_genesis(1598918400, 52613770, 0x1E0377AE, 1, 50 * 10 ** 8)


class RegTest:
    name = "regtest"
    p2p_port = 18444
    rpc_port = 18445
    magic = "fabfb5da"
    addresses = []
    genesis = create_genesis(1296688602, 2, 0x207FFFFF, 1, 50 * 10 ** 8)
