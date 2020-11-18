from dataclasses import dataclass
from typing import List, Tuple

from btclib import varint
from btclib.utils import bytesio_from_binarydata

from btclib_node.p2p.messages import add_headers


@dataclass
class Notfound:
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
        return add_headers("notfound", payload)


@dataclass
class Reject:
    message: str
    code: int
    reason: str
    data: str

    @classmethod
    def deserialize(cls, data):
        stream = bytesio_from_binarydata(data)
        message = stream.read(varint.decode(stream)).decode()
        code = int.from_bytes(stream.read(1), "little")
        reason = stream.read(varint.decode(stream)).decode()
        data = stream.read(32)
        return cls(message, code, reason, data)

    def serialize(self):
        payload = varint.encode(len(self.message))
        payload += self.message.encode()
        payload += self.code.to_bytes(1, "little")
        payload += varint.encode(len(self.reason))
        payload += self.reason.encode()
        payload += bytes.fromhex(self.data)[::-1]
        return add_headers("reject", payload)
