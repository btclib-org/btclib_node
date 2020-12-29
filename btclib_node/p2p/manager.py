import asyncio
import random
import socket
import threading
import time
import traceback
from collections import deque

import uvloop

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
        self.handshake_messages = deque()
        self.addresses = []
        self.loop = uvloop.new_event_loop()
        self.port = port
        self.last_connection_id = -1

    def create_connection(self, reader, writer):
        self.last_connection_id += 1
        conn = Connection(reader, writer, self, self.last_connection_id)
        self.connections[self.last_connection_id] = conn
        return conn

    async def server_connection(self, reader, writer):
        conn = self.create_connection(reader, writer)
        task = asyncio.create_task(conn.run())
        conn.task = task
        await task

    async def async_connect(self, address):
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.settimeout(0)
        try:
            client.connect(address)
        except BlockingIOError:
            await asyncio.sleep(1)
            try:
                client.getpeername()
                reader, writer = await asyncio.open_connection(sock=client)
                conn = self.create_connection(reader, writer)
                task = asyncio.run_coroutine_threadsafe(conn.run(), self.loop)
                conn.task = task
            except socket.error:
                client.close()

    # def connect(self, address):
    #     client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #     client.settimeout(1)
    #     try:
    #         client.connect(address)
    #         conn = self.create_connection(client, address)
    #         asyncio.run_coroutine_threadsafe(conn.run(), self.loop)
    #     except OSError:
    #         pass

    def remove_connection(self, id):
        if id in self.connections.keys():
            self.connections[id].stop()
            self.connections.pop(id)

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
        server = await asyncio.start_server(
            self.server_connection, "0.0.0.0", self.port, loop=self.loop
        )

        async with server:
            await server.serve_forever()

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
