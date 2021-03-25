from dataclasses import dataclass
from typing import List

from btclib import varint
from btclib.utils import bytesio_from_binarydata

from btclib_node.p2p.address import NetworkAddress
from btclib_node.p2p.messages import add_headers


@dataclass
class Addr:
    addresses: List[NetworkAddress]

    @classmethod
    def deserialize(cls, data):
        stream = bytesio_from_binarydata(data)
        len_addresses = varint.decode(stream)
        addresses = []
        for x in range(len_addresses):
            addresses.append(NetworkAddress.deserialize(stream))
        return cls(addresses=addresses)

    def serialize(self):
        payload = varint.encode(len(self.addresses))
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
