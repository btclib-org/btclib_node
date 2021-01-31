from dataclasses import dataclass
from typing import List, Tuple

from btclib import varint
from btclib.utils import bytesio_from_binarydata

from btclib_node.p2p.messages import add_headers


@dataclass
class Getdata:
    inventory: List[Tuple[int, str]]

    @classmethod
    def deserialize(cls, data):
        stream = bytesio_from_binarydata(data)
        inventory_length = varint.decode(stream)
        inventory = []
        for x in range(inventory_length):
            item_type = int.from_bytes(stream.read(4), "little")
            item_hash = stream.read(32)[::-1].hex()
            inventory.append((item_type, item_hash))
        return cls(inventory)

    def serialize(self):
        payload = varint.encode(len(self.inventory))
        for item in self.inventory:
            payload += item[0].to_bytes(4, "little")
            payload += bytes.fromhex(item[1])[::-1]
        return add_headers("getdata", payload)


@dataclass
class Getblocks:
    version: int
    block_hashes: List[str]
    hash_stop: str

    @classmethod
    def deserialize(cls, data):
        stream = bytesio_from_binarydata(data)
        version = int.from_bytes(stream.read(4), "little")
        block_hashes = []
        for x in range(varint.decode(stream)):
            block_hash = stream.read(32)[::-1].hex()
            block_hashes.append(block_hash)
        hash_stop = stream.read(32)[::-1].hex()
        return cls(version=version, block_hashes=block_hashes, hash_stop=hash_stop)

    def serialize(self):
        payload = self.version.to_bytes(4, "little")
        payload += varint.encode(len(self.block_hashes))
        for hash in self.block_hashes:
            payload += bytes.fromhex(hash)[::-1]
        payload += bytes.fromhex(self.hash_stop)[::-1]
        return add_headers("getblocks", payload)


@dataclass
class Getheaders:
    version: int
    block_hashes: List[str]
    hash_stop: str

    @classmethod
    def deserialize(cls, data):
        stream = bytesio_from_binarydata(data)
        version = int.from_bytes(stream.read(4), "little")
        block_hashes = []
        for x in range(varint.decode(stream)):
            block_hash = stream.read(32)[::-1].hex()
            block_hashes.append(block_hash)
        hash_stop = stream.read(32)[::-1].hex()
        return cls(version=version, block_hashes=block_hashes, hash_stop=hash_stop)

    def serialize(self):
        payload = self.version.to_bytes(4, "little")
        payload += varint.encode(len(self.block_hashes))
        for hash in self.block_hashes:
            payload += bytes.fromhex(hash)[::-1]
        payload += bytes.fromhex(self.hash_stop)[::-1]
        return add_headers("getheaders", payload)


@dataclass
class Getblocktxn:
    blockhash: str
    indexes: List[int]

    @classmethod
    def deserialize(cls, data):
        stream = bytesio_from_binarydata(data)
        blockhash = stream.read(32)[::-1].hex()
        num_indexes = varint.decode(stream)
        indexes = []
        for x in range(num_indexes):
            indexes.append(varint.decode(stream))
        return cls(blockhash=blockhash, indexes=indexes)

    def serialize(self):
        payload = bytes.fromhex(self.blockhash)[::-1]
        payload += varint.encode(len(self.indexes))
        for id in self.indexes:
            payload += varint.encode(id)
        return add_headers("getblocktxn", payload)


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
