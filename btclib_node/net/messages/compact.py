from dataclasses import dataclass

from btclib_node.net.messages import add_headers


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
