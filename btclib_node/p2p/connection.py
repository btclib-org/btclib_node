import asyncio
import random
import re
import time

from btclib_node.p2p.constants import ConnectionStatus, ProtocolVersion
from btclib_node.p2p.messages import WrongChecksumError, get_payload, verify_headers
from btclib_node.p2p.messages.handshake import Version
from btclib_node.structures import NetworkAddress
from btclib_node.utils import to_ipv6


class Connection:
    def __init__(self, reader, writer, manager, id):
        super().__init__()
        self.manager = manager
        self.loop = manager.loop
        self.reader = reader
        self.writer = writer
        self.sock = self.writer.transport.get_extra_info("socket")
        self.address = self.sock.getpeername()
        self.node = manager.node
        self.id = id
        self.buffer = b""
        self.task = None

        self.status = ConnectionStatus.Open

        self.version_message = None
        self.block_download_queue = []

    def stop(self, cancel_task=True):
        self.status = ConnectionStatus.Closed
        if self.task and cancel_task:
            self.task.cancel()
        self.writer.close()

    async def run(self, connect=True):
        await self.send_version()
        while self.status < ConnectionStatus.Closed:
            data = await self.reader.read(1024)
            if not data:
                return self.stop(cancel_task=False)
            try:
                self.buffer += data
                self.parse_messages()
            except Exception:
                return self.stop(cancel_task=False)

    async def _send(self, data):
        data = bytes.fromhex(self.node.chain.magic) + data
        self.writer.write(data)
        await self.writer.drain()

    async def async_send(self, msg):
        await self._send(msg.serialize())

    def send(self, msg):
        asyncio.run_coroutine_threadsafe(self.async_send(msg), self.loop)

    async def send_version(self):
        services = 1032 + 1 * 0  # TODO: for now we don't have blocks, only headers
        version = Version(
            version=ProtocolVersion,
            services=services,
            timestamp=int(time.time()),
            addr_recv=NetworkAddress(
                0, to_ipv6(self.sock.getpeername()[0]), self.sock.getpeername()[1]
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

    def parse_messages(self):
        while True:
            if not self.buffer:
                return
            try:
                verify_headers(self.buffer)
                message_length = int.from_bytes(self.buffer[16:20], "little")
                message = get_payload(self.buffer)
                self.buffer = self.buffer[24 + message_length :]
                if message[0] in ("version", "verack"):
                    self.manager.handshake_messages.append((*message, self.id))
                elif message[0] in ("ping", "pong"):
                    self.manager.messages.appendleft((*message, self.id))
                else:
                    self.manager.messages.append((*message, self.id))
            except WrongChecksumError:
                # https://stackoverflow.com/questions/30945784/how-to-remove-all-characters-before-a-specific-character-in-python
                self.buffer = re.sub(
                    f"^.*?{self.node.chain.magic}".encode(),
                    self.node.chain.magic.encode(),
                    self.buffer,
                )
            except ValueError:
                return

    def __repr__(self):
        try:
            out = f"Connection to {self.sock.getpeername()[0]}:{self.sock.getpeername()[1]}"
        except OSError:
            out = "Broken connection"
        return out
