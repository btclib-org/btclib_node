from btclib_node.p2p.messages.address import Addr, Getaddr
from btclib_node.p2p.messages.compact import Sendcmpct
from btclib_node.p2p.messages.data import Block as BlockMsg
from btclib_node.p2p.messages.data import Headers, Inv
from btclib_node.p2p.messages.data import Tx as TxMsg
from btclib_node.p2p.messages.errors import Notfound
from btclib_node.p2p.messages.getdata import Getdata, Getheaders, Sendheaders


# called when a connection has been made
def connection_made(node, _, conn):
    conn.send(Sendcmpct(0, 1))
    conn.send(Sendheaders())
    conn.send(Getaddr())
    block_locators = node.index.get_block_locator_hashes()
    conn.send(Getheaders(7015, block_locators, "00" * 32))


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
    header_status = node.index.get_header_status(block.header.hash)

    if not header_status.downloaded:
        print(block.header.hash)
    if block.header.hash in conn.block_download_queue:
        conn.block_download_queue.remove(block.header.hash)

    header_status.downloaded = True
    node.index.insert_header_status(header_status)


# TODO: do not ask for a block if we are still downloading old blocks
def inv(node, msg, conn):
    inv = Inv.deserialize(msg)
    if node.status == "Syncing":
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
        except:
            continue
    headers = valid_headers
    added = node.index.add_headers(headers)
    if len(headers) == 2000 and added:  # we have to require more headers
        block_locators = node.index.get_block_locator_hashes()
        conn.send(Getheaders(7015, block_locators, "00" * 32))
    else:
        node.status = "Synced"


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


callbacks = {
    "inv": inv,
    "tx": tx,
    "block": block,
    "getdata": getdata,
    "getheaders": getheaders,
    "connection_made": connection_made,
    "headers": headers,
    "notfound": not_found,
    "addr": addr,
}
