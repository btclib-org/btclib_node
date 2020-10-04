import random
from dataclasses import dataclass

from btclib.utils import bytesio_from_binarydata

from btclib_node.net.messages import add_headers


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
