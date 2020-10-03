#!/usr/bin/env python3

# Copyright (C) 2017-2020 The btclib developers
#
# This file is part of btclib. It is subject to the license terms in the
# LICENSE file found in the top-level directory of this distribution.
#
# No part of btclib including this file, may be copied, modified, propagated,
# or distributed except according to the terms contained in the LICENSE file.

import random
from hashlib import sha256
import struct
from btclib import varint
from btclib.utils import bytesio_from_binarydata
from dataclasses import dataclass
from structures import NetworkAddress
from typing import List, Tuple

from btclib.blocks import Block
from btclib.tx import Tx


class WrongChecksumError(Exception):
    pass


# does not add network_string
def add_headers(name: str, payload: bytes):
    command = name + ((12 - len(name)) * "\00")
    payload_len = struct.pack("I", len(payload))
    checksum = sha256(sha256(payload).digest()).digest()[:4]
    return command.encode() + payload_len + checksum + payload


def verify_headers(message: bytes):
    payload_len = int.from_bytes(message[16:20], "little")
    checksum = message[20:24]
    payload = message[24 : 24 + payload_len]
    if len(payload) != payload_len:
        raise Exception("Not enough data")
    if checksum != sha256(sha256(payload).digest()).digest()[:4]:
        raise WrongChecksumError("Wrong checksum, the message might have been tampered")
    return True


def get_payload(message: bytes):
    verify_headers(message)
    message_name = message[4:16].rstrip(b"\x00").decode()
    payload_len = int.from_bytes(message[16:20], "little")
    payload = message[24 : 24 + payload_len]
    return (message_name, payload)


@dataclass
class Version:
    version: int
    services: int
    timestamp: int
    addr_recv: NetworkAddress
    addr_from: NetworkAddress
    nonce: int
    user_agent: str
    start_height: int
    relay: bool

    @classmethod
    def deserialize(cls, data):
        stream = bytesio_from_binarydata(data)
        version = int.from_bytes(stream.read(4), "little")
        services = int.from_bytes(stream.read(8), "little")
        timestamp = int.from_bytes(stream.read(8), "little")
        addr_recv = NetworkAddress.deserialize(stream)
        addr_from = NetworkAddress.deserialize(stream)
        nonce = int.from_bytes(stream.read(8), "little")
        user_agent_len = varint.decode(stream)
        user_agent = stream.read(user_agent_len)
        start_height = int.from_bytes(stream.read(4), "little")
        relay = bool(int.from_bytes(stream.read(1), "little"))
        return cls(
            version=version,
            services=services,
            timestamp=timestamp,
            addr_recv=addr_recv,
            addr_from=addr_from,
            nonce=nonce,
            user_agent=user_agent,
            start_height=start_height,
            relay=relay,
        )

    def serialize(self):
        payload = self.version.to_bytes(4, "little")
        payload += self.services.to_bytes(8, "little")
        payload += self.timestamp.to_bytes(8, "little")
        payload += self.addr_recv.serialize()
        payload += self.addr_from.serialize()
        payload += self.nonce.to_bytes(8, "little")
        if self.user_agent:
            payload += varint.encode(len(self.user_agent))
            payload += self.user_agent.encode()
        payload += self.start_height.to_bytes(4, "little")
        payload += self.relay.to_bytes(1, "little")
        return add_headers("version", payload)


@dataclass
class Verack:
    @classmethod
    def deserialize(cls, data):
        return cls()

    def serialize(self):
        return add_headers("verack", b"")


@dataclass
class Addr:
    addresses: List[Tuple[int, NetworkAddress]]

    @classmethod
    def deserialize(cls, data):
        stream = bytesio_from_binarydata(data)
        len_addresses = varint.decode(stream)
        addresses = []
        for x in range(len_addresses):
            address_timestamp = int.from_bytes(stream.read(8), "little")
            address = stream.read(22)
            addresses.append((address_timestamp, address))
        return cls(addresses=addresses)

    def serialize(self):
        payload = varint.encode(len(self.addresses))
        for address_timestamp, address in self.addresses:
            payload += address_timestamp.to_bytes(8, "little")
            payload += address.serialize()
        return add_headers("addr", payload)


@dataclass
class Inv:
    @classmethod
    def deserialize(cls, data):
        return cls()

    def serialize(self):
        return add_headers("inv", b"")


@dataclass
class Getdata:
    @classmethod
    def deserialize(cls, data):
        return cls()

    def serialize(self):
        return add_headers("getdata", b"")


@dataclass
class Notfound:
    @classmethod
    def deserialize(cls, data):
        return cls()

    def serialize(self):
        return add_headers("notfound", b"")


@dataclass
class Getblocks:
    version: int
    block_locator_hashes = List[str]
    hash_stop = str

    @classmethod
    def deserialize(cls, data):
        return cls()

    def serialize(self):
        payload = self.version.to_bytes(4, "little")
        payload += varint.encode(len(self.block_locator_hashes))
        for hash in self.block_locator_hashes:
            payload += bytes.fromhex(hash)[::-1]
        payload += bytes.fromhex(self.hash_stop)[::-1]
        return add_headers("getblocks", payload)


@dataclass
class Getheaders:
    version: int
    block_locator_hashes = List[str]
    hash_stop = str

    @classmethod
    def deserialize(cls, data):
        return cls()

    def serialize(self):
        payload = self.version.to_bytes(4, "little")
        payload += varint.encode(len(self.block_locator_hashes))
        for hash in self.block_locator_hashes:
            payload += bytes.fromhex(hash)[::-1]
        payload += bytes.fromhex(self.hash_stop)[::-1]
        return add_headers("getheaders", payload)


@dataclass
class Tx:
    data: Tx

    @classmethod
    def deserialize(cls, data):
        return cls(Tx.deserialize(data))

    def serialize(self):
        return add_headers("tx", self.data.serialize())


@dataclass
class Block:
    data: Block

    @classmethod
    def deserialize(cls, data):
        return cls(Block.deserialize(data))

    def serialize(self):
        return add_headers("block", self.data.serialize())


@dataclass
class Headers:
    @classmethod
    def deserialize(cls, data):
        return cls()

    def serialize(self):
        return add_headers("headers", b"")


@dataclass
class Getaddr:
    @classmethod
    def deserialize(cls, data):
        return cls()

    def serialize(self):
        return add_headers("getaddr", b"")


@dataclass
class Mempool:
    @classmethod
    def deserialize(cls, data):
        return cls()

    def serialize(self):
        return add_headers("mempool", b"")


@dataclass
class Ping:
    nonce: int

    def __init__(self, nonce=None):
        if not nonce:
            self.nonce = random.randint(0, 2 ** 64 - 1)
        else:
            self.nonce = nonce

    @classmethod
    def deserialize(cls, data):
        stream = bytesio_from_binarydata(data)
        nonce = int.from_bytes(stream.read(8), "little")
        return cls(nonce=nonce)

    def serialize(self):
        return add_headers("ping", self.nonce.to_bytes(8, "little"))


@dataclass
class Pong:
    nonce: int

    @classmethod
    def deserialize(cls, data):
        stream = bytesio_from_binarydata(data)
        nonce = int.from_bytes(stream.read(8), "little")
        return cls(nonce=nonce)

    def serialize(self):
        return add_headers("pong", self.nonce.to_bytes(8, "little"))


@dataclass
class Reject:
    @classmethod
    def deserialize(cls, data):
        return cls()

    def serialize(self):
        return add_headers("reject", b"")


@dataclass
class Filterload:
    @classmethod
    def deserialize(cls, data):
        return cls()

    def serialize(self):
        return add_headers("filterload", b"")


@dataclass
class Filteradd:
    @classmethod
    def deserialize(cls, data):
        return cls()

    def serialize(self):
        return add_headers("filteradd", b"")


@dataclass
class Filterclear:
    @classmethod
    def deserialize(cls, data):
        return cls()

    def serialize(self):
        return add_headers("filterclear", b"")


@dataclass
class Merkleblock:
    @classmethod
    def deserialize(cls, data):
        return cls()

    def serialize(self):
        return add_headers("merkleblock", b"")


@dataclass
class Sendheaders:
    @classmethod
    def deserialize(cls, data):
        return cls()

    def serialize(self):
        return add_headers("sendheaders", b"")


@dataclass
class Freefilter:
    @classmethod
    def deserialize(cls, data):
        return cls()

    def serialize(self):
        return add_headers("freefilter", b"")


@dataclass
class Sendcmpct:
    @classmethod
    def deserialize(cls, data):
        return cls()

    def serialize(self):
        return add_headers("sendcmpt", b"")


@dataclass
class Cmptcblock:
    @classmethod
    def deserialize(cls, data):
        return cls()

    def serialize(self):
        return add_headers("cmptblock", b"")


@dataclass
class Getblocktxn:
    @classmethod
    def deserialize(cls, data):
        return cls()

    def serialize(self):
        return add_headers("getblocktxn", b"")


@dataclass
class Blocktxn:
    @classmethod
    def deserialize(cls, data):
        return cls()

    def serialize(self):
        return add_headers("blocktxn", b"")
