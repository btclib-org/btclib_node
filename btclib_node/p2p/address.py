import asyncio
import random
import socket
from dataclasses import dataclass
from ipaddress import AddressValueError, IPv6Address

from btclib.utils import bytesio_from_binarydata


def to_ipv6(ip):
    try:
        return IPv6Address(ip)
    except AddressValueError:
        return IPv6Address(f"::ffff:{ip}")


@dataclass
class NetworkAddress:
    time: int = 0
    services: int = 0
    ip: IPv6Address = to_ipv6("::")
    port: int = 0

    @classmethod
    def deserialize(cls, data, version_msg=False):
        stream = bytesio_from_binarydata(data)
        time = 0 if version_msg else int.from_bytes(stream.read(4), "little")
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
        ip = self.ip.ipv4_mapped
        if not ip:
            return
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.settimeout(0)
        try:
            client.connect((str(ip), self.port))
        except BlockingIOError:
            await asyncio.sleep(1)
            try:
                client.getpeername()
                return client
            except socket.error:
                client.close()


class PeerDB:
    def __init__(self, chain, data_dir):
        self.chain = chain
        self.data_dir = data_dir
        self.addresses = {}

    def is_empty(self):
        return not len(self.addresses)

    async def get_dns_nodes(self):
        chain = self.chain
        loop = asyncio.get_running_loop()
        addresses = []
        for dns_server in chain.addresses:
            try:
                ips = await loop.getaddrinfo(dns_server, chain.port)
            except socket.gaierror:
                continue
            for ip in ips:
                addresses.append(ip[4])
        for address in list(set(addresses)):
            address = NetworkAddress(ip=to_ipv6(address[0]), port=address[1])
            self.addresses[str(address.ip)] = address

    def random_address(self):
        return self.addresses[random.choice(list(self.addresses))]

    def add_addresses(self, addresses):
        for address in addresses:
            if len(self.addresses) >= 10000:
                continue
            key = str(address.ip)
            if key not in self.addresses:
                self.addresses[key] = address
