import time

from btclib.exceptions import BTClibValueError

from btclib_node.constants import NodeStatus, P2pConnStatus, ProtocolVersion
from btclib_node.p2p.messages.address import Addr, Getaddr
from btclib_node.p2p.messages.compact import Sendcmpct
from btclib_node.p2p.messages.data import Block as BlockMsg
from btclib_node.p2p.messages.data import Headers, Inv
from btclib_node.p2p.messages.data import Tx as TxMsg
from btclib_node.p2p.messages.errors import Notfound
from btclib_node.p2p.messages.getdata import Getdata, Getheaders, Sendheaders
from btclib_node.p2p.messages.handshake import Verack, Version
from btclib_node.p2p.messages.ping import Ping, Pong


def version(node, msg, conn):
    version_msg = Version.deserialize(msg)

    conn.version_message = version_msg
    if version_msg.nonce in node.p2p_manager.nonces:  # connection to ourselves
        conn.stop()
        return

    if version_msg.version < ProtocolVersion:
        conn.stop()
        return
    if not version_msg.services & 8:  # we only connect to witness nodes
        conn.stop()
        return
    if not version_msg.services & 1 and node.status >= NodeStatus.BlockSynced:
        conn.stop()
        return

    conn.send(Verack())


def verack(node, msg, conn):
    if not conn.version_message:
        conn.stop()
        return
    conn.status = P2pConnStatus.Connected
    conn.send(Sendcmpct(0, 1))
    conn.send(Sendheaders())
    conn.send(Getaddr())
    block_locators = node.index.get_block_locator_hashes()
    conn.send(Getheaders(ProtocolVersion, block_locators, b"\x00" * 32))
    node.logger.info(
        f"Connected to {conn.client.getpeername()[0]}:{conn.client.getpeername()[1]}"
    )


def ping(node, msg, conn):
    nonce = Ping.deserialize(msg).nonce
    conn.send(Pong(nonce))


def pong(node, msg, conn):
    nonce = Pong.deserialize(msg).nonce
    if conn.ping_sent:
        if conn.ping_nonce != nonce:
            conn.stop()
            return
        conn.latency = time.time() - conn.ping_sent
        conn.ping_sent = 0
        conn.ping_nonce = 0


# TODO: send our node location
def getaddr(node, msg, conn):
    pass


def addr(node, msg, conn):
    addresses = Addr.deserialize(msg).addresses
    node.p2p_manager.peer_db.add_addresses(addresses)


# TODO: sends to many messages
# TODO: check if we have already sent and inv containing this tx
def tx(node, msg, conn):
    tx = TxMsg.deserialize(msg).tx
    node.mempool.add_tx(tx)
    node.p2p_manager.sendall(Inv([(1, tx.id)]))


def block(node, msg, conn):

    block = BlockMsg.deserialize(msg, check_validity=False).block
    block_hash = block.header.hash

    if block_hash in conn.block_download_queue:
        conn.block_download_queue.remove(block_hash)

    block_info = node.index.get_block_info(block_hash)

    if not block_info.downloaded:
        try:
            block.assert_valid()
        except Exception as e:  # should set block to invalid
            raise e
        node.block_db.add_block(block)
        node.logger.info(f"Received new block with hash:{block_hash.hex()}")
        block_info.downloaded = True
        node.index.insert_block_info(block_info)


def inv(node, msg, conn):
    inv = Inv.deserialize(msg)
    if node.status < NodeStatus.BlockSynced:
        return

    transactions = [x[1] for x in inv.inventory if x[0] in [1, 0x40000001]]
    if blocks := [x[1] for x in inv.inventory if x[0] in [2, 0x40000002]]:
        block_locators = node.index.get_block_locator_hashes()
        conn.send(Getheaders(ProtocolVersion, block_locators, blocks[-1]))

    if missing_tx := node.mempool.get_missing(transactions):
        conn.send(Getdata([(0x40000001, tx) for tx in missing_tx]))


def getdata(node, msg, conn):
    getdata = Getdata.deserialize(msg)
    transactions = [x[1] for x in getdata.inventory if x[0] in [1, 0x40000001]]
    blocks = [x[1] for x in getdata.inventory if x[0] in [2, 0x40000002]]
    for txid in transactions:
        if tx := node.mempool.get_tx(txid):
            conn.send(TxMsg(tx))
    for block_hash in blocks:
        if block := node.block_db.get_block(block_hash):
            conn.send(BlockMsg(block))


def headers(node, msg, conn):
    headers = Headers.deserialize(msg).headers
    valid_headers = []
    for header in headers:
        try:
            valid_headers.append(header)
        except BTClibValueError:
            continue
    headers = valid_headers
    added = node.index.add_headers(headers)
    # TODO: now it doesn't support long reorganizations (> 2000 headers)
    if len(headers) == 2000 and added:  # we have to require more headers
        block_locators = node.index.get_block_locator_hashes()
        conn.send(Getheaders(ProtocolVersion, block_locators, b"\x00" * 32))
    elif node.status == NodeStatus.SyncingHeaders:
        node.status = NodeStatus.HeaderSynced


def getheaders(node, msg, conn):
    getheaders = Getheaders.deserialize(msg)
    if headers := node.index.get_headers_from_locators(
        getheaders.block_hashes, getheaders.hash_stop
    ):
        conn.send(Headers(headers))


def not_found(node, msg, conn):
    missing = Notfound.deserialize(msg)
    node.logger.warning(f"Missing objects:{missing}")


handshake_callbacks = {"version": version, "verack": verack}

callbacks = {
    "ping": ping,
    "pong": pong,
    "inv": inv,
    "tx": tx,
    "block": block,
    "getdata": getdata,
    "getheaders": getheaders,
    "headers": headers,
    "notfound": not_found,
    "addr": addr,
    "getaddr": getaddr,
}
