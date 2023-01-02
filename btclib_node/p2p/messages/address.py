from dataclasses import dataclass
from typing import List

from btclib import var_int
from btclib.utils import bytesio_from_binarydata

from btclib_node.p2p.address import NetworkAddress
from btclib_node.p2p.messages import add_headers


@dataclass
class Addr:
    addresses: List[NetworkAddress]

    @classmethod
    def deserialize(cls, data):
        stream = bytesio_from_binarydata(data)
        len_addresses = var_int.parse(stream)
        addresses = [NetworkAddress.deserialize(stream) for _ in range(len_addresses)]
        return cls(addresses=addresses)

    def serialize(self):
        payload = var_int.serialize(len(self.addresses))
        for address in self.addresses:
            payload += address.serialize()
        return add_headers("addr", payload)


@dataclass
class Getaddr:
    @classmethod
    def deserialize(cls, data):
        return cls()

    def serialize(self):
        return add_headers("getaddr", b"")
