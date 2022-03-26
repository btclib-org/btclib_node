from dataclasses import dataclass

from btclib import var_int
from btclib.utils import bytesio_from_binarydata

from btclib_node.p2p.address import NetworkAddress
from btclib_node.p2p.messages import add_headers


@dataclass
class Version:
    version: int
    services: int
    timestamp: int
    addr_recv: NetworkAddress
    addr_from: NetworkAddress
    nonce: int
    user_agent: str
    start_height: int
    relay: bool

    @classmethod
    def deserialize(cls, data):
        stream = bytesio_from_binarydata(data)
        version = int.from_bytes(stream.read(4), "little")
        services = int.from_bytes(stream.read(8), "little")
        timestamp = int.from_bytes(stream.read(8), "little")
        addr_recv = NetworkAddress.deserialize(stream, version_msg=True)
        addr_from = NetworkAddress.deserialize(stream, version_msg=True)
        nonce = int.from_bytes(stream.read(8), "little")
        user_agent_len = var_int.parse(stream)
        user_agent = stream.read(user_agent_len).decode()
        start_height = int.from_bytes(stream.read(4), "little")
        relay = bool(int.from_bytes(stream.read(1), "little"))
        return cls(
            version=version,
            services=services,
            timestamp=timestamp,
            addr_recv=addr_recv,
            addr_from=addr_from,
            nonce=nonce,
            user_agent=user_agent,
            start_height=start_height,
            relay=relay,
        )

    def serialize(self):
        payload = self.version.to_bytes(4, "little")
        payload += self.services.to_bytes(8, "little")
        payload += self.timestamp.to_bytes(8, "little")
        payload += self.addr_recv.serialize(version_msg=True)
        payload += self.addr_from.serialize(version_msg=True)
        payload += self.nonce.to_bytes(8, "little")
        if self.user_agent:
            payload += var_int.serialize(len(self.user_agent))
            payload += self.user_agent.encode()
        else:
            payload += var_int.serialize(0)
        payload += self.start_height.to_bytes(4, "little")
        payload += self.relay.to_bytes(1, "little")
        return add_headers("version", payload)


@dataclass
class Verack:
    @classmethod
    def deserialize(cls, data):
        return cls()

    def serialize(self):
        return add_headers("verack", b"")
