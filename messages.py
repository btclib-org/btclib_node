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
from ipaddress import IPv6Address


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
class NetworkAddress:
    services: int
    ip: IPv6Address
    port: int

    @classmethod
    def deserialize(cls, data):
        stream = bytesio_from_binarydata(data)
        services = int.from_bytes(stream.read(8), "little")
        ip = IPv6Address(stream.read(16))
        port = int.from_bytes(stream.read(2), "big")
        return cls(services=services, ip=ip, port=port)

    def serialize(self):
        payload = self.services.to_bytes(8, "little")
        payload += self.ip.packed
        payload += self.port.to_bytes(2, "big")
        return payload


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


class Verack:
    @classmethod
    def deserialize(cls, data):
        return cls()

    def serialize(self):
        return add_headers("verack", b"")


class Addr:
    def __init__(self):
        super().__init__(name="verack")


class Inv:
    def __init__(self):
        super().__init__(name="inv")


class Getdata:
    def __init__(self):
        super().__init__(name="getdata")


class Notfound:
    def __init__(self):
        super().__init__(name="notfound")


class Getblocks:
    def __init__(self):
        super().__init__(name="getblocks")
        self.hashes = []
        self.hash_stop = b""

    @property
    def raw(self):
        out = (70015).to_bytes(4, "little")
        out += varint.encode(len(self.hashes))
        for hash in self.hashes:
            out += hash
        out += self.hash_stop
        return out


class Getheaders:
    def __init__(self):
        super().__init__(name="getheaders")
        self.hashes = []
        self.hash_stop = b""

    @property
    def raw(self):
        out = (70015).to_bytes(4, "little")
        out += varint.encode(len(self.hashes))
        for hash in self.hashes:
            out += hash
        out += self.hash_stop
        return out


class Tx:
    def __init__(self):
        super().__init__(name="tx")


class Block:
    def __init__(self):
        super().__init__(name="block")


class Headers:
    def __init__(self):
        super().__init__(name="headers")


class Getaddr:
    def __init__(self):
        super().__init__(name="getaddr")


class Mempool:
    def __init__(self):
        super().__init__(name="mempool")


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


class Reject:
    def __init__(self):
        super().__init__(name="reject")


class Filterload:
    def __init__(self):
        super().__init__(name="filterload")


class Filteradd:
    def __init__(self):
        super().__init__(name="filteradd")


class Filterclear:
    def __init__(self):
        super().__init__(name="filterclear")


class Merckleblock:
    def __init__(self):
        super().__init__(name="merckleblock")


class Sendheaders:
    def __init__(self):
        super().__init__(name="sendheaders")


class Freefilter:
    def __init__(self):
        super().__init__(name="freefilter")


class Sendcmpct:
    def __init__(self):
        super().__init__(name="sendcmpct")


class Cmptcblock:
    def __init__(self):
        super().__init__(name="cmptcblock")


class Getblocktxn:
    def __init__(self):
        super().__init__(name="getblocktxn")


class Blocktxn:
    def __init__(self):
        super().__init__(name="blocktxn")
