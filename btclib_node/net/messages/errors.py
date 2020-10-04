from dataclasses import dataclass

from btclib_node.net.messages import add_headers


@dataclass
class Notfound:
    @classmethod
    def deserialize(cls, data):
        return cls()

    def serialize(self):
        return add_headers("notfound", b"")


@dataclass
class Reject:
    @classmethod
    def deserialize(cls, data):
        return cls()

    def serialize(self):
        return add_headers("reject", b"")
