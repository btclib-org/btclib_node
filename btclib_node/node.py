import os
import threading

from btclib_node.net.connection_manager import ConnectionManager
from btclib_node.net.messages.address import Addr
from btclib_node.net.messages.data import Headers, Inv
from btclib_node.net.messages.getdata import Getheaders


class Node(threading.Thread):
    def __init__(self, net_port):
        super().__init__()

        self.magic = "f9beb4d9"
        self.connection_manager = ConnectionManager(self, net_port)
        self.connection_manager.start()
        self.data_dir = os.path.join(os.getcwd(), "test_data")
        os.makedirs(self.data_dir, exist_ok=True)

        self.lock = threading.Lock()
        self.terminate_flag = threading.Event()

    def run(self):
        while not self.terminate_flag.is_set():
            if not len(self.connection_manager.messages):
                continue
            message = self.connection_manager.messages.popleft()
            if message[0] == "addr":
                print(Addr.deserialize(message[1]).addresses)
                # pass
            elif message[0] == "getaddr":
                pass
            elif message[0] == "sendcmpt":
                pass
            elif message[0] == "cmptblock":
                pass
            elif message[0] == "tx":
                pass
            elif message[0] == "block":
                pass
            elif message[0] == "headers":
                # print(Headers.deserialize(message[1]))
                pass
            elif message[0] == "blocktxn":
                pass
            elif message[0] == "inv":
                pass
                # print(Inv.deserialize(message[1]))
            elif message[0] == "notfound":
                pass
            elif message[0] == "filterload":
                pass
            elif message[0] == "filteradd":
                pass
            elif message[0] == "filterclear":
                pass
            elif message[0] == "merkleblock":
                pass
            elif message[0] == "feefilter":
                pass
            elif message[0] == "filterclear":
                pass
            elif message[0] == "getdata":
                pass
            elif message[0] == "getblocks":
                pass
            elif message[0] == "getheaders":
                pass
                # print(Getheaders.deserialize(message[1]))
            elif message[0] == "getblocktxn":
                pass
            elif message[0] == "mempool":
                pass
            elif message[0] == "sendheaders":
                pass
            elif message[0] == "ping":
                pass
            elif message[0] == "pong":
                pass

    def stop(self):
        self.terminate_flag.set()
        self.connection_manager.stop()

    def connect(self, host, port):
        self.connection_manager.connect(host, port)
