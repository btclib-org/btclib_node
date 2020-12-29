import asyncio
import socket
import threading
import time
from collections import deque

import uvloop

from btclib_node.rpc.connection import Connection


class RpcManager(threading.Thread):
    def __init__(self, node, port):
        super().__init__()
        self.node = node
        self.chain = node.chain
        self.connections = {}
        self.messages = deque()
        self.loop = uvloop.new_event_loop()
        self.port = port
        self.last_connection_id = -1

    async def create_connection(self, reader, writer):
        self.last_connection_id += 1
        conn = Connection(reader, writer, self, self.last_connection_id, self.loop)
        self.connections[self.last_connection_id] = conn
        task = asyncio.create_task(conn.run())
        conn.task = task
        await task

    def remove_connection(self, id):
        if id in self.connections.keys():
            self.connections[id].stop()
            self.connections.pop(id)

    async def server(self, loop):
        server = await asyncio.start_server(
            self.create_connection, "0.0.0.0", self.port, loop=self.loop
        )

        async with server:
            await server.serve_forever()

    def run(self):
        loop = self.loop
        asyncio.set_event_loop(loop)
        asyncio.run_coroutine_threadsafe(self.server(loop), loop)
        loop.run_forever()

    def stop(self):
        for conn in self.connections.values():
            conn.close()
        for task in asyncio.all_tasks(self.loop):
            task.cancel()
        self.loop.call_soon_threadsafe(self.loop.stop)
        time.sleep(1)
        self.loop.run_until_complete(self.loop.shutdown_asyncgens())
        self.loop.close()
