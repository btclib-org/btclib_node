import asyncio
import socket
import threading
import time
from collections import deque
from contextlib import suppress

from btclib_node.constants import NodeStatus, P2pConnStatus
from btclib_node.p2p.address import NetworkAddress
from btclib_node.p2p.connection import Connection
from btclib_node.p2p.messages.data import Tx
from btclib_node.p2p.messages.ping import Ping


class P2pManager(threading.Thread):
    def __init__(self, node, port, peer_db):
        super().__init__()
        self.node = node
        self.logger = node.logger
        self.port = port
        self.peer_db = peer_db

        self.connections = {}
        self.messages = deque()
        self.handshake_messages = deque()
        self.nonces = []
        self.last_connection_id = -1

        self.loop = asyncio.new_event_loop()

    def create_connection(self, client, address, inbound):
        client.settimeout(0.0)
        self.last_connection_id += 1
        conn = Connection(self, client, address, self.last_connection_id, inbound)
        self.connections[self.last_connection_id] = conn
        task = asyncio.run_coroutine_threadsafe(conn.run(), self.loop)
        conn.task = task

    def remove_connection(self, id):
        if id in self.connections.keys():
            self.connections[id].stop()
            self.connections.pop(id)

    async def async_connect(self, address):
        client = await address.connect()
        if client:
            self.create_connection(client, address, False)

    def connect(self, address):
        asyncio.run_coroutine_threadsafe(
            self.async_connect(address), self.loop
        )

    async def manage_connections(self, loop):
        while True:
            now = time.time()
            for conn in self.connections.copy().values():
                if conn.status == P2pConnStatus.Closed:
                    self.remove_connection(conn.id)
                if now - conn.last_receive > 120:
                    if not conn.ping_sent:
                        conn.send_ping()
                    elif now - conn.ping_sent > 120:
                        self.remove_connection(conn.id)
            if self.node.status < NodeStatus.HeaderSynced:
                connection_num = 1
            else:
                connection_num = 10
            if len(self.connections) < connection_num and not self.peer_db.is_empty:
                already_connected = [conn.address for conn in self.connections.values()]
                try:
                    address = self.peer_db.random_address()
                    if address not in already_connected:
                        sock = await address.connect()
                        if sock:
                            self.create_connection(sock, address, False)
                except Exception:
                    self.logger.exception("Exception occurred")
            await asyncio.sleep(0.1)

    async def server(self, loop):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(("0.0.0.0", self.port))
        server_socket.listen()
        server_socket.settimeout(0.0)
        with server_socket:
            while True:
                sock, ip_and_port = await loop.sock_accept(server_socket)
                address = NetworkAddress.from_ip_and_port(*ip_and_port)
                self.create_connection(sock, address, True)

    def run(self):
        self.logger.info("Starting P2P manager")
        loop = self.loop
        asyncio.set_event_loop(loop)
        asyncio.run_coroutine_threadsafe(self.peer_db.get_addr_from_dns(), loop)
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

    def broadcast_raw_transaction(self, tx):
        self.sendall(Tx(tx))

    def ping_all(self):
        for conn in self.connections.copy().values():
            conn.send_ping()
