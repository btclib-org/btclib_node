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
        try:
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
            if type(body) != list:
                body = [body]
            self.manager.messages.append((body, self.id))
        except Exception:
            self.client.close()

    async def async_send(self, response):
        if len(response) == 1:
            response = response[0]
        output_str = json.dumps(response, separators=(",", ":"))
        response = "HTTP/1.1 200 OK\n"
        response += "Content-Type: application/json\n"
        response += f"Content-Length: {len(output_str)+1}\n"
        response += "\n"  # Important!
        response += output_str
        response += "\n"
        await self.loop.sock_sendall(self.client, response.encode())
        self.client.close()

    def send(self, response):
        asyncio.run_coroutine_threadsafe(self.async_send(response), self.loop)

    def __repr__(self):
        try:
            out = f"Connection to {self.client.getpeername()[0]}:{self.client.getpeername()[1]}"
        except OSError:
            out = "Broken connection"
        return out
