import asyncio
import socket
import threading
from collections import deque

from btclib_node.net.connection import Connection


class ConnectionManager(threading.Thread):
    def __init__(self, net, port):
        super().__init__()
        self.net = net
        self.magic = net.magic
        self.connections = {}
        self.terminate_flag = threading.Event()
        self.messages = deque()
        self.loop = asyncio.new_event_loop()
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(("0.0.0.0", self.port))
        self.server_socket.listen()
        self.server_socket.settimeout(0.0)

    def create_connection(self, loop, client):
        id = max(self.connections.keys()) + 1 if self.connections else 0
        new_connection = Connection(loop, client, self, id)
        self.connections[id] = new_connection  # TODO
        return new_connection

    def remove_connection(self, id):
        del self.connections[id]

    async def __run(self, loop):
        sock = self.server_socket
        with sock:
            while True:
                client, addr = await loop.sock_accept(sock)
                asyncio.run_coroutine_threadsafe(
                    self.create_connection(loop, client).run(), loop
                )

    def run(self):
        asyncio.set_event_loop(self.loop)
        asyncio.run_coroutine_threadsafe(self.__run(self.loop), self.loop)
        self.loop.run_forever()

    def stop(self):
        self.loop.stop()

    def connect(self, host, port):
        target = socket.getaddrinfo(host, port)[0][4]
        if len(target) == 2:  # ipv4
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        elif len(target) == 4:  # ipv6
            client = socket.socket(socket.AF_INET6, socket.SOCK_STREAM, 0)
        try:
            client.settimeout(1)
            client.connect(target)
        except OSError:
            return
        client.settimeout(0.0)
        conn = self.create_connection(self.loop, client)
        asyncio.run_coroutine_threadsafe(conn.run(), self.loop)

    def send(self, msg, id):
        self.connections[id].send(msg)

    def sendall(self, msg):
        for conn in self.connections:
            conn.send(msg)
