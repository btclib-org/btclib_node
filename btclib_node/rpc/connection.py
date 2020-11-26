import asyncio

try:
    from http_parser.parser import HttpParser
except ImportError:
    from http_parser.pyparser import HttpParser
import json


class Connection:
    def __init__(self, loop, client, manager, id):
        super().__init__()
        self.loop = loop
        self.client = client
        self.manager = manager
        self.id = id
        self.rpc_id = ""
        self.messages = []
        self.buffer = b""
        self.task = None

    def close(self):
        if self.task:
            self.task.cancel()
        self.client.close()

    async def run(self):
        p = HttpParser()
        body = []
        while True:
            data = await self.loop.sock_recv(self.client, 1024)
            if not data:
                break
            recved = len(data)
            nparsed = p.execute(data, recved)
            assert nparsed == recved
            if p.is_partial_body():
                body.append(p.recv_body())
            if p.is_message_complete():
                break
        body = json.loads(body[0])
        self.rpc_id = body["id"]
        msg_type = body["method"]
        parameters = body["params"]
        self.manager.messages.append((msg_type, parameters, self.id))

    async def async_send(self, result, error=None):
        output = {"result": result, "error": error, "id": self.rpc_id}
        output_str = json.dumps(output, separators=(",", ":"))
        response = (
            "HTTP/1.1 200 OK\n"
            + "Content-Type: application/json\n"
            + f"Content-Length: {len(output_str)+1}\n"
            + "\n"  # Important!
            + output_str
            + "\n"
        ).encode()
        await self.loop.sock_sendall(self.client, response)
        self.client.close()

    def send(self, result, error=None):
        asyncio.run_coroutine_threadsafe(self.async_send(result, error), self.loop)

    def __repr__(self):
        try:
            out = f"Connection to {self.client.getpeername()[0]}:{self.client.getpeername()[1]}"
        except OSError:
            out = "Broken connection"
        return out
