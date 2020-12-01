import asyncio
import enum
import random
import re
import time

from btclib_node.p2p.messages import WrongChecksumError, get_payload, verify_headers
from btclib_node.p2p.messages.handshake import Verack, Version
from btclib_node.p2p.messages.ping import Ping, Pong
from btclib_node.structures import NetworkAddress
from btclib_node.utils import to_ipv6

Status = enum.IntEnum("Status", ["Open", "Version", "Connected", "Closed"])


class Connection:
    def __init__(self, loop, client, manager, id):
        super().__init__()
        self.loop = loop
        self.client = client
        self.manager = manager
        self.id = id
        self.buffer = b""
        self.task = None

        self.status = Status.Open
        self.messages = []

        self.version_message = None
        self.block_download_queue = []

    def stop(self, cancel_task=True):
        self.status = Status.Closed
        if self.task and cancel_task:
            self.task.cancel()
        self.client.close()

    async def run(self):
        await self.send_version()
        while self.status < Status.Closed:
            data = await self.loop.sock_recv(self.client, 1024)
            if not data:
                return self.stop(cancel_task=False)
            try:
                self.buffer += data
                self.parse_messages()
                if self.messages:
                    if self.status < Status.Connected:
                        await self.validate_handshake()
                    if self.status == Status.Connected:
                        await self.handle_messages()
                    else:
                        return self.stop(cancel_task=False)
            except Exception:
                return self.stop(cancel_task=False)

    async def _send(self, data):
        data = bytes.fromhex(self.manager.magic) + data
        await self.loop.sock_sendall(self.client, data)

    async def async_send(self, msg):
        await self._send(msg.serialize())

    def send(self, msg):
        asyncio.run_coroutine_threadsafe(self.async_send(msg), self.loop)

    async def send_version(self):
        services = 1032 + 1 * 0  # TODO: for now we don't have blocks, only headers
        version = Version(
            version=70015,
            services=services,
            timestamp=int(time.time()),
            addr_recv=NetworkAddress(
                0, to_ipv6(self.client.getpeername()[0]), self.client.getpeername()[1]
            ),  # TODO
            addr_from=NetworkAddress(
                services, to_ipv6("0.0.0.0"), self.manager.port
            ),  # TODO
            nonce=random.randint(0, 0xFFFFFFFFFFFF),
            user_agent="/Btclib/",
            start_height=0,  # TODO
            relay=True,  # TODO
        )
        await self.async_send(version)

    def accept_version(self, version_message):
        if version_message.version != 70015:
            return False
        # for now we only connect to full nodes
        if not version_message.services & 1:
            return False
        # we only connect to witness nodes
        if not version_message.services & 8:
            return False
        return True

    async def validate_handshake(self):
        if self.status < Status.Version:
            if self.messages:
                # first message must be version
                if not self.messages[0][0] == "version":
                    return self.stop(cancel_task=False)
                else:
                    version_message = Version.deserialize(self.messages[0][1])
                    if self.accept_version(version_message):
                        self.version_message = version_message
                        await self.async_send(Verack())
                        self.messages = self.messages[1:]
                        self.status = Status.Version
                    else:
                        return self.stop(cancel_task=False)
        if self.status == Status.Version:
            if self.messages:
                # second message must be verack
                if not self.messages[0][0] == "verack":
                    return self.stop(cancel_task=False)
                else:
                    self.messages = self.messages[1:]
                    self.status = Status.Connected
                    self.manager.messages.append(("connection_made", "", self.id))

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
        try:
            out = f"Connection to {self.client.getpeername()[0]}:{self.client.getpeername()[1]}"
        except OSError:
            out = "Broken connection"
        return out
