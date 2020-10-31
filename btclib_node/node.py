import os
import threading
import time

from btclib.tx import Tx

from btclib_node.mempool import Mempool
from btclib_node.net.connection_manager import ConnectionManager
from btclib_node.net.messages.data import Inv
from btclib_node.net.messages.data import Tx as TxMessage


# TODO: sends to many messages
def tx(node, msg, conn_id):
    tx = Tx.deserialize(msg)
    node.mempool.add_tx(tx)
    node.connection_manager.sendall(Inv([(1, tx.txid)]))


def inv(node, msg, conn_id):
    inv = Inv.deserialize(msg)
    transactions = [x[1] for x in inv.inventory if x[0] == 1]
    # blocks = [x[1] for x in inv.inventory if x[0] == 2]
    gettransaction_msg = node.mempool.get_missing(transactions)
    if gettransaction_msg.inventory:
        node.connection_manager.send(gettransaction_msg, conn_id)


def getdata(node, msg, conn_id):
    inv = Inv.deserialize(msg)
    transactions = [x[1] for x in inv.inventory if x[0] == 1]
    # blocks = [x[1] for x in inv.inventory if x[0] == 2]
    for tx in transactions:
        if tx in node.mempool.transactions:
            node.connection_manager.send(
                TxMessage(node.mempool.transactions[tx]), conn_id
            )


class Node(threading.Thread):
    def __init__(self, net_port):
        super().__init__()

        self.magic = "f9beb4d9"
        self.connection_manager = ConnectionManager(self, net_port)
        self.connection_manager.start()
        self.mempool = Mempool({})
        self.data_dir = os.path.join(os.getcwd(), "test_data")
        os.makedirs(self.data_dir, exist_ok=True)

        self.lock = threading.Lock()
        self.terminate_flag = threading.Event()

    def run(self):
        callbacks = {"inv": inv, "tx": tx, "getdata": getdata}
        while not self.terminate_flag.is_set():
            if not len(self.connection_manager.messages):
                continue
            msg_type, msg, conn_id = self.connection_manager.messages.popleft()
            print(time.time(), msg_type)
            if msg_type in callbacks:
                try:
                    callbacks[msg_type](self, msg, conn_id)
                except Exception:
                    pass

    def stop(self):
        self.terminate_flag.set()
        self.connection_manager.stop()

    def connect(self, host, port):
        self.connection_manager.connect(host, port)
