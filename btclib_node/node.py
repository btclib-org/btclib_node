import threading

from btclib_node.net.connection_manager import ConnectionManager


class Node(threading.Thread):
    def __init__(self, net_port):
        super().__init__()

        self.magic = "f9beb4d9"
        self.connection_manager = ConnectionManager(self, net_port)
        self.connection_manager.start()

        self.lock = threading.Lock()
        self.terminate_flag = threading.Event()

    def run(self):
        while not self.terminate_flag.is_set():
            pass

    def stop(self):
        self.terminate_flag.set()
        self.connection_manager.stop()

    def connect(self, host, port):
        self.connection_manager.connect(host, port)
