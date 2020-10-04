from dataclasses import dataclass
from typing import List

from btclib import varint

from btclib_node.net.messages import add_headers


@dataclass
class Getdata:
    @classmethod
    def deserialize(cls, data):
        return cls()

    def serialize(self):
        return add_headers("getdata", b"")


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
class Getblocktxn:
    @classmethod
    def deserialize(cls, data):
        return cls()

    def serialize(self):
        return add_headers("getblocktxn", b"")


@dataclass
class Mempool:
    @classmethod
    def deserialize(cls, data):
        return cls()

    def serialize(self):
        return add_headers("mempool", b"")


@dataclass
class Sendheaders:
    @classmethod
    def deserialize(cls, data):
        return cls()

    def serialize(self):
        return add_headers("sendheaders", b"")
