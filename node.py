import threading
import socket
import time

from connection import Connection


class Node(threading.Thread):
    def __init__(self, port=8333):
        super().__init__()

        self.connections = []
        self.magic = "f9beb4d9"

        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(("0.0.0.0", self.port))
        self.server_socket.listen()
        self.server_socket.settimeout(0.0)

        self.lock = threading.Lock()
        self.terminate_flag = threading.Event()

    def run(self):
        while not self.terminate_flag.is_set():
            try:
                conn, address = self.server_socket.accept()
                new_connection = Connection(conn, address, self)
                new_connection.start()
                self.connections.append(new_connection)
            except socket.error:
                pass
            with self.lock:
                for conn in self.connections:
                    if not conn.is_alive():
                        print("dead")
                        self.connections.remove(conn)
            time.sleep(0.1)

    def stop(self):
        self.terminate_flag.set()
        self.server_socket.close()
        for conn in self.connections:
            conn.stop()
        for conn in self.connections:
            conn.join()
            self.connections.remove(conn)

    def connect(self, ip, port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((ip, port))
        new_connection = Connection(sock, [ip, port], self)
        new_connection.start()
        self.connections.append(new_connection)

    def sendall(self, data):
        for conn in self.connections:
            conn.send(data)
