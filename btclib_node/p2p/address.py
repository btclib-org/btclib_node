import asyncio
import socket
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
    time: int = 0
    services: int = 0
    ip: IPv6Address = to_ipv6("::")
    port: int = 0

    @classmethod
    def deserialize(cls, data, version_msg=False):
        stream = bytesio_from_binarydata(data)
        if not version_msg:
            time = int.from_bytes(stream.read(4), "little")
        else:
            time = 0
        services = int.from_bytes(stream.read(8), "little")
        a = stream.read(16)
        ip = IPv6Address(a)
        port = int.from_bytes(stream.read(2), "big")
        return cls(time=time, services=services, ip=ip, port=port)

    def serialize(self, version_msg=False):
        payload = b""
        if not version_msg:
            payload += self.time.to_bytes(4, "little")
        payload += self.services.to_bytes(8, "little")
        payload += self.ip.packed
        payload += self.port.to_bytes(2, "big")
        return payload

    async def connect(self):
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.settimeout(0)
        try:
            ip = self.ip.ipv4_mapped
            if not ip:
                return
            client.connect((str(ip), self.port))
        except BlockingIOError:
            await asyncio.sleep(1)
            try:
                client.getpeername()
                return client
            except socket.error:
                client.close()
