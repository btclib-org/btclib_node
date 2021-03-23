import asyncio
import random
import socket
import threading
import time
from collections import deque
from contextlib import suppress

from btclib_node.constants import NodeStatus, P2pConnStatus
from btclib_node.p2p.connection import Connection
from btclib_node.p2p.messages.ping import Ping


async def get_dns_nodes(chain):
    loop = asyncio.get_running_loop()
    addresses = []
    for dns_server in chain.addresses:
        try:
            ips = await loop.getaddrinfo(dns_server, chain.port)
        except socket.gaierror:
            continue
        for ip in ips:
            addresses.append(ip[4])
    addresses = list(set(addresses))
    random.shuffle(addresses)
    return addresses


class P2pManager(threading.Thread):
    def __init__(self, node, port):
        super().__init__()
        self.node = node
        self.logger = node.logger
        self.chain = node.chain
        self.connections = {}
        self.messages = deque()
        self.handshake_messages = deque()
        self.addresses = []
        self.nonces = []
        self.loop = asyncio.new_event_loop()
        self.port = port
        self.last_connection_id = -1

    def create_connection(self, client, address):
        client.settimeout(0.0)
        self.last_connection_id += 1
        conn = Connection(self, client, address, self.last_connection_id)
        self.connections[self.last_connection_id] = conn
        task = asyncio.run_coroutine_threadsafe(conn.run(), self.loop)
        conn.task = task

    def remove_connection(self, id):
        if id in self.connections.keys():
            self.connections[id].stop()
            self.connections.pop(id)

    async def async_connect(self, address):
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.settimeout(0)
        try:
            client.connect(address)
        except BlockingIOError:
            await asyncio.sleep(1)
            try:
                client.getpeername()
                self.create_connection(client, address)
            except socket.error:
                client.close()

    def connect(self, address):
        asyncio.run_coroutine_threadsafe(self.async_connect(address), self.loop)

    async def manage_connections(self, loop):
        self.addresses = await get_dns_nodes(self.chain)
        while True:
            now = time.time()
            for conn in self.connections.copy().values():
                if conn.status == P2pConnStatus.Closed:
                    self.remove_connection(conn.id)
                if now - conn.last_receive > 120:
                    if not conn.ping_sent:
                        ping_msg = Ping()
                        conn.send(ping_msg)
                        conn.ping_sent = now
                        conn.ping_nonce = ping_msg.nonce
                    elif now - conn.ping_sent > 120:
                        self.remove_connection(conn.id)
            await asyncio.sleep(0.1)
            if self.node.status < NodeStatus.HeaderSynced:
                self.connection_num = 1
            else:
                self.connection_num = 10
            if not self.addresses:
                continue
            already_connected = [conn.address for conn in self.connections.values()]
            self.addresses = list(set(self.addresses))
            addresses = [x for x in self.addresses if tuple(x) not in already_connected]
            random.shuffle(addresses)
            if len(self.connections) < self.connection_num and addresses:
                try:
                    await self.async_connect(addresses[0])
                except Exception:
                    self.logger.exception("Exception occurred")

    async def server(self, loop):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(("0.0.0.0", self.port))
        server_socket.listen()
        server_socket.settimeout(0.0)
        with server_socket:
            while True:
                client, addr = await loop.sock_accept(server_socket)
                self.create_connection(client, addr)

    def run(self):
        self.logger.info("Starting P2P manager")
        loop = self.loop
        asyncio.set_event_loop(loop)
        asyncio.run_coroutine_threadsafe(self.server(loop), loop)
        asyncio.run_coroutine_threadsafe(self.manage_connections(loop), loop)
        loop.run_forever()

    def stop(self):
        self.loop.call_soon_threadsafe(self.loop.stop)
        for conn in self.connections.copy().values():
            conn.stop()
        while self.loop.is_running():
            pass
        pending = asyncio.all_tasks(self.loop)
        for task in pending:
            task.cancel()
            with suppress(asyncio.CancelledError):
                self.loop.run_until_complete(task)
        self.loop.close()
        self.logger.info("Stopping P2P Manager")

    def send(self, msg, id):
        if id in self.connections:
            self.connections[id].send(msg)

    def sendall(self, msg):
        for conn in self.connections.copy().values():
            conn.send(msg)
