import asyncio
import random
import socket
import threading
import time
import traceback
from collections import deque

from btclib_node.p2p.connection import Connection


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
        self.chain = node.chain
        self.connections = {}
        self.messages = deque()
        self.addresses = []
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
            for conn in self.connections.copy().values():
                if conn.status == 4:
                    self.remove_connection(conn.id)
            await asyncio.sleep(0.1)
            self.connection_num = 1 if self.node.status == "Syncing" else 10
            self.addresses = list(set(self.addresses))
            random.shuffle(self.addresses)
            if len(self.connections) < self.connection_num:
                try:
                    address = self.addresses[0]
                    already_connected = [
                        conn.address for conn in self.connections.values()
                    ]
                    if tuple(address) not in already_connected:
                        await self.async_connect(self.addresses[0])
                except Exception:
                    traceback.print_exc()

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
        loop = self.loop
        asyncio.set_event_loop(loop)
        asyncio.run_coroutine_threadsafe(self.server(loop), loop)
        asyncio.run_coroutine_threadsafe(self.manage_connections(loop), loop)
        loop.run_forever()

    def stop(self):
        for conn in self.connections.values():
            conn.stop()
        for task in asyncio.all_tasks(self.loop):
            task.cancel()
        self.loop.call_soon_threadsafe(self.loop.stop)
        time.sleep(1)
        self.loop.run_until_complete(self.loop.shutdown_asyncgens())
        self.loop.close()

    def send(self, msg, id):
        if id in self.connections:
            self.connections[id].send(msg)

    def sendall(self, msg):
        for conn in self.connections.values():
            conn.send(msg)
