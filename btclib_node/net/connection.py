import asyncio
import random
import re
import time

from btclib_node.net.messages import WrongChecksumError, get_payload, verify_headers
from btclib_node.net.messages.handshake import Verack, Version
from btclib_node.net.messages.ping import Ping, Pong
from btclib_node.structures import NetworkAddress
from btclib_node.utils import to_ipv6


class Connection:
    def __init__(self, loop, client, manager, id):
        super().__init__()
        self.loop = loop
        self.client = client
        self.manager = manager
        self.id = id
        self.messages = []
        self.buffer = b""
        self.received_version = False
        self.connected = False

    async def run(self):
        with self.client:
            await self.send_version()
            while True:
                data = await self.loop.sock_recv(self.client, 1024)
                if not data:
                    self.remove_connection()
                self.buffer += data
                self.parse_messages()
                if self.messages:
                    await self.handle_messages()

    async def _send(self, data):
        data = bytes.fromhex(self.manager.magic) + data
        await self.loop.sock_sendall(self.client, data)

    async def async_send(self, msg):
        await self._send(msg.serialize())

    def send(self, msg):
        asyncio.run_coroutine_threadsafe(self.async_send(msg), self.loop)

    async def send_version(self):
        services = 1  # TODO
        version = Version(
            version=70015,  # TODO
            services=services,
            timestamp=int(time.time()),
            addr_recv=NetworkAddress(
                1, to_ipv6(self.client.getpeername()[0]), self.client.getpeername()[1]
            ),  # TODO
            addr_from=NetworkAddress(services, to_ipv6("0.0.0.0"), 8333),  # TODO
            nonce=random.randint(0, 0xFFFFFFFFFFFF),
            user_agent="/Btclib/",
            start_height=0,  # TODO
            relay=True,  # TODO
        )
        await self.async_send(version)

    def accept_version(self, version_message):
        return True

    async def validate_handshake(self):
        if not self.received_version:
            if self.messages:
                # first message must be version
                if not self.messages[0][0] == "version":
                    self.stop()
                else:
                    version_message = Version.deserialize(self.messages[0][1])
                    if self.accept_version(version_message):
                        await self.async_send(Verack())
                        self.messages = self.messages[1:]
                        self.received_version = True
                    else:
                        self.stop()
        if self.received_version and not self.connected:
            if self.messages:
                # second message must be verack
                if not self.messages[0][0] == "verack":
                    self.stop()
                else:
                    self.messages = self.messages[1:]
                    self.connected = True

    def parse_messages(self):
        while True:
            if not self.buffer:
                return
            try:
                verify_headers(self.buffer)
                message_length = int.from_bytes(self.buffer[16:20], "little")
                message = get_payload(self.buffer)
                self.buffer = self.buffer[24 + message_length :]
                self.messages.append(message)
            except WrongChecksumError:
                # https://stackoverflow.com/questions/30945784/how-to-remove-all-characters-before-a-specific-character-in-python
                self.buffer = re.sub(
                    f"^.*?{self.manager.magic}".encode(),
                    self.manager.magic.encode(),
                    self.buffer,
                )
            except Exception:
                return

    async def handle_messages(self):
        if not self.connected:
            await self.validate_handshake()
        if self.connected:
            if "ping" in (x[0] for x in self.messages):
                ping_msg = next(x for x in self.messages if x[0] == "ping")
                ping = Ping.deserialize(ping_msg[1])
                await self.async_send(Pong(ping.nonce))
                self.messages.remove(ping_msg)

    def remove_connection(self):
        self.manager.remove_connection(self.id)

    def __repr__(self):
        return f"Connection to {self.client.getpeername()[0]}:{self.client.getpeername()[1]}"
