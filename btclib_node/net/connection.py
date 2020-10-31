import asyncio
import enum
import random
import re
import time

from btclib_node.net.messages import WrongChecksumError, get_payload, verify_headers
from btclib_node.net.messages.compact import Sendcmpct
from btclib_node.net.messages.getdata import Sendheaders
from btclib_node.net.messages.handshake import Verack, Version
from btclib_node.net.messages.ping import Ping, Pong
from btclib_node.structures import NetworkAddress
from btclib_node.utils import to_ipv6

State = enum.IntEnum("State", ["Open", "Version", "Connected", "Closed"])


class Connection:
    def __init__(self, loop, client, manager, id):
        super().__init__()
        self.loop = loop
        self.client = client
        self.manager = manager
        self.id = id
        self.messages = []
        self.buffer = b""
        self.state = State.Open
        self.task = None

    def stop(self):
        self.state = State.Closed
        if self.task:
            self.task.cancel()

    async def run(self):
        with self.client:
            await self.send_version()
            while self.state < State.Closed:
                data = await self.loop.sock_recv(self.client, 1024)
                if not data:
                    return self.stop()
                try:
                    self.buffer += data
                    self.parse_messages()
                    if self.messages:
                        if self.state < State.Connected:
                            await self.validate_handshake()
                        if self.state == State.Connected:
                            await self.handle_messages()
                        else:
                            return self.stop()
                except Exception as e:
                    print(e)
                    raise e

    async def _send(self, data):
        data = bytes.fromhex(self.manager.magic) + data
        await self.loop.sock_sendall(self.client, data)

    async def async_send(self, msg):
        await self._send(msg.serialize())

    def send(self, msg):
        asyncio.run_coroutine_threadsafe(self.async_send(msg), self.loop)

    async def send_version(self):
        services = 1032  # TODO
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
        return version_message.version == 70015

    async def validate_handshake(self):
        if self.state < State.Version:
            if self.messages:
                # first message must be version
                if not self.messages[0][0] == "version":
                    return self.stop()
                else:
                    version_message = Version.deserialize(self.messages[0][1])
                    if self.accept_version(version_message):
                        await self.async_send(Verack())
                        self.messages = self.messages[1:]
                        self.state = State.Version
                    else:
                        return self.stop()
        if self.state == State.Version:
            if self.messages:
                # second message must be verack
                if not self.messages[0][0] == "verack":
                    return self.stop()
                else:
                    self.messages = self.messages[1:]
                    self.state = State.Connected
                    await self.async_send(Sendcmpct(0, 1))
                    await self.async_send(Sendheaders())

    def parse_messages(self):
        while True:
            if not self.buffer:
                return
            try:
                verify_headers(self.buffer)
                message_length = int.from_bytes(self.buffer[16:20], "little")
                message = get_payload(self.buffer)
                self.buffer = self.buffer[24 + message_length :]
                if message[0] in ("version", "verack", "ping", "pong"):
                    self.messages.append(message)
                elif message[0] in ("addr", "getaddr"):
                    self.manager.messages.append((*message, self.id))
                else:
                    self.manager.messages.append((*message, self.id))
            except WrongChecksumError:
                # https://stackoverflow.com/questions/30945784/how-to-remove-all-characters-before-a-specific-character-in-python
                self.buffer = re.sub(
                    f"^.*?{self.manager.magic}".encode(),
                    self.manager.magic.encode(),
                    self.buffer,
                )
            except ValueError:
                return

    async def handle_messages(self):
        for message in self.messages:
            if message[0] == "ping":
                ping = Ping.deserialize(message[1])
                await self.async_send(Pong(ping.nonce))
            self.messages.pop(0)

    def __repr__(self):
        return f"Connection to {self.client.getpeername()[0]}:{self.client.getpeername()[1]}"
