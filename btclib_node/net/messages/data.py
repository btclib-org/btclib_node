from dataclasses import dataclass

from btclib.blocks import Block
from btclib.tx import Tx

from btclib_node.net.messages import add_headers


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
class Blocktxn:
    @classmethod
    def deserialize(cls, data):
        return cls()

    def serialize(self):
        return add_headers("blocktxn", b"")


@dataclass
class Inv:
    @classmethod
    def deserialize(cls, data):
        return cls()

    def serialize(self):
        return add_headers("inv", b"")
