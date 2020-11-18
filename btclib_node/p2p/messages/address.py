from dataclasses import dataclass
from typing import List, Tuple

from btclib import varint
from btclib.utils import bytesio_from_binarydata

from btclib_node.p2p.messages import add_headers
from btclib_node.structures import NetworkAddress


@dataclass
class Addr:
    addresses: List[Tuple[int, NetworkAddress]]

    @classmethod
    def deserialize(cls, data):
        stream = bytesio_from_binarydata(data)
        len_addresses = varint.decode(stream)
        addresses = []
        for x in range(len_addresses):
            address_timestamp = int.from_bytes(stream.read(4), "little")
            address = NetworkAddress.deserialize(stream)
            addresses.append((address_timestamp, address))
        return cls(addresses=addresses)

    def serialize(self):
        payload = varint.encode(len(self.addresses))
        for address_timestamp, address in self.addresses:
            payload += address_timestamp.to_bytes(8, "little")
            payload += address.serialize()
        return add_headers("addr", payload)


@dataclass
class Getaddr:
    @classmethod
    def deserialize(cls, data):
        return cls()

    def serialize(self):
        return add_headers("getaddr", b"")
