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
    if version_msg.version < ProtocolVersion:
        conn.stop()
        return
    # for now we only connect to full nodes
    if not version_msg.services & 1:
        conn.stop()
        return
    # we only connect to witness nodes
    if not version_msg.services & 8:
        conn.stop()
        return

    conn.version_message = version_msg
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
    conn.send(Getheaders(ProtocolVersion, block_locators, "00" * 32))


def ping(node, msg, conn):
    nonce = Ping.deserialize(msg).nonce
    conn.send(Pong(nonce))


def pong(node, msg, conn):
    pass


def addr(node, msg, conn):
    addresses = Addr.deserialize(msg).addresses
    addresses = [x for x in addresses if x[1].ip.ipv4_mapped]
    addresses = [(x[1].ip.ipv4_mapped.compressed, x[1].port) for x in addresses]
    node.p2p_manager.addresses.extend(addresses)


# TODO: sends to many messages
# TODO: check if we have already sent and inv containing this tx
def tx(node, msg, conn):
    tx = TxMsg.deserialize(msg).tx
    node.mempool.add_tx(tx)
    node.p2p_manager.sendall(Inv([(1, tx.txid)]))


def block(node, msg, conn):
    block = BlockMsg.deserialize(msg).block
    block.assert_valid()

    if block.header.hash in conn.block_download_queue:
        conn.block_download_queue.remove(block.header.hash)

    block_info = node.index.get_block_info(block.header.hash)

    if not block_info.downloaded:
        block_info.downloaded = True
        node.index.insert_block_info(block_info)
        node.block_db.add_block(block)
        print(block.header.hash)


def inv(node, msg, conn):
    inv = Inv.deserialize(msg)
    if node.status < NodeStatus.BlockSynced:
        return

    transactions = [x[1] for x in inv.inventory if x[0] == 1 or x[0] == 0x40000001]
    blocks = [x[1] for x in inv.inventory if x[0] == 2 or x[0] == 0x40000002]
    if blocks:
        block_locators = node.index.get_block_locator_hashes()
        conn.send(Getheaders(7015, block_locators, blocks[-1]))

    missing_tx = node.mempool.get_missing(transactions)
    if missing_tx:
        conn.send(Getdata([(0x40000001, tx) for tx in missing_tx]))


def getdata(node, msg, conn):
    getdata = Getdata.deserialize(msg)
    transactions = [x[1] for x in getdata.inventory if x[0] == 1 or x[0] == 0x40000001]
    # blocks = [x[1] for x in getdata.inventory if x[0] == 2 or x[0] == 0x40000002]
    for tx in transactions:
        if tx in node.mempool.transactions:
            conn.send(TxMsg(node.mempool.transactions[tx]))


def headers(node, msg, conn):
    headers = Headers.deserialize(msg).headers
    valid_headers = []
    for header in headers:
        try:
            header.assert_valid()
            valid_headers.append(header)
        except BTClibValueError:
            continue
    headers = valid_headers
    added = node.index.add_headers(headers)
    # TODO: now it doesn't support long reorganizations (> 20000 headers)
    if len(headers) == 2000 and added:  # we have to require more headers
        block_locators = node.index.get_block_locator_hashes()
        conn.send(Getheaders(ProtocolVersion, block_locators, "00" * 32))
    else:
        if node.status == NodeStatus.SyncingHeaders:
            node.status = NodeStatus.HeaderSynced


def getheaders(node, msg, conn):
    getheaders = Getheaders.deserialize(msg)
    headers = node.index.get_headers_from_locators(
        getheaders.block_hashes, getheaders.hash_stop
    )
    if headers:
        return Headers(headers)


def not_found(node, msg, conn):
    missing = Notfound.deserialize(msg)
    print("Missing objects:", missing)


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
}
