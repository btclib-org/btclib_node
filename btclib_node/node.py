import os
import threading
import time

from btclib.tx import Tx

from btclib_node.chainstate import Chainstate
from btclib_node.index import BlockIndex
from btclib_node.mempool import Mempool
from btclib_node.net.connection_manager import ConnectionManager
from btclib_node.net.messages.compact import Sendcmpct
from btclib_node.net.messages.data import Headers, Inv
from btclib_node.net.messages.data import Tx as TxMessage
from btclib_node.net.messages.getdata import Getdata, Getheaders, Sendheaders


# called when a connection has been made
def connection_made(node, _, conn_id):
    node.connection_manager.send(Sendcmpct(0, 1), conn_id)
    node.connection_manager.send(Sendheaders(), conn_id)
    block_locators = node.index.get_block_locator_hashes()
    node.connection_manager.send(Getheaders(7015, block_locators, "00" * 32), conn_id)


# TODO: sends to many messages
# TODO: check if we have already sent and inv containing this tx
def tx(node, msg, conn_id):
    tx = Tx.deserialize(msg)
    node.mempool.add_tx(tx)
    node.connection_manager.sendall(Inv([(1, tx.txid)]))


# TODO: do not ask for a block if we are still downloading old blocks
def inv(node, msg, conn_id):
    inv = Inv.deserialize(msg)
    if node.status == "Syncing":
        return
    transactions = [x[1] for x in inv.inventory if x[0] == 1 or x[0] == 0x40000001]
    blocks = [x[1] for x in inv.inventory if x[0] == 2 or x[0] == 0x40000002]
    if blocks:
        block_locators = node.index.get_block_locator_hashes()
        node.connection_manager.send(
            Getheaders(7015, block_locators, blocks[-1]), conn_id
        )

    missing_tx = node.mempool.get_missing(transactions)
    if missing_tx:
        node.connection_manager.send(
            Getdata([(0x40000001, tx) for tx in missing_tx]), conn_id
        )


def getdata(node, msg, conn_id):
    getdata = Getdata.deserialize(msg)
    transactions = [x[1] for x in getdata.inventory if x[0] == 1 or x[0] == 0x40000001]
    # blocks = [x[1] for x in getdata.inventory if x[0] == 2 or x[0] == 0x40000002]
    for tx in transactions:
        if tx in node.mempool.transactions:
            node.connection_manager.send(
                TxMessage(node.mempool.transactions[tx]), conn_id
            )


def headers(node, msg, conn_id):
    headers = Headers.deserialize(msg).headers
    added = node.index.add_headers(headers)
    if len(headers) == 2000 and added:  # we have to require more headers
        block_locators = node.index.get_block_locator_hashes()
        node.connection_manager.send(
            Getheaders(7015, block_locators, "00" * 32), conn_id
        )
    else:
        node.status = "Synced"


def getheaders(node, msg, conn_id):
    getheaders = Getheaders.deserialize(msg)
    headers = node.index.get_headers(getheaders.block_hashes, getheaders.hash_stop)
    if headers:
        return Headers(headers)


class Node(threading.Thread):
    def __init__(self, net_port):
        super().__init__()

        self.magic = "f9beb4d9"

        self.connection_manager = ConnectionManager(self, net_port)
        self.index = BlockIndex(
            {}, ["000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8ce26f"]
        )
        self.chainstate = Chainstate({})
        self.mempool = Mempool({})

        self.data_dir = os.path.join(os.getcwd(), "test_data")
        os.makedirs(self.data_dir, exist_ok=True)
        self.lock = threading.Lock()
        self.terminate_flag = threading.Event()

        self.connection_manager.start()

        self.status = "Syncing"

    def run(self):
        callbacks = {
            "inv": inv,
            "tx": tx,
            "getdata": getdata,
            "getheaders": getheaders,
            "connection_made": connection_made,
            "headers": headers,
        }
        while not self.terminate_flag.is_set():
            if len(self.connection_manager.messages):
                msg_type, msg, conn_id = self.connection_manager.messages.popleft()
                # print(time.time(), msg_type)
                if msg_type in callbacks:
                    try:
                        callbacks[msg_type](self, msg, conn_id)
                    except Exception as e:
                        print(e)
                        pass

    def stop(self):
        self.terminate_flag.set()
        self.connection_manager.stop()

    def connect(self, host, port):
        self.connection_manager.connect(host, port)
