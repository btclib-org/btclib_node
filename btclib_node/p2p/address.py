from dataclasses import dataclass
from ipaddress import AddressValueError, IPv6Address

from btclib.utils import bytesio_from_binarydata


def to_ipv6(ip):
    try:
        return IPv6Address(ip)
    except AddressValueError:
        return IPv6Address("::ffff:" + ip)


@dataclass
class NetworkAddress:
    services: int
    ip: IPv6Address
    port: int

    @classmethod
    def deserialize(cls, data):
        stream = bytesio_from_binarydata(data)
        services = int.from_bytes(stream.read(8), "little")
        a = stream.read(16)
        ip = IPv6Address(a)
        port = int.from_bytes(stream.read(2), "big")
        return cls(services=services, ip=ip, port=port)

    def serialize(self):
        payload = self.services.to_bytes(8, "little")
        payload += self.ip.packed
        payload += self.port.to_bytes(2, "big")
        return payload
