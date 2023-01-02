from btclib_node.constants import P2pConnStatus


def get_best_block_hash(node, conn, _):
    return node.index.header_index[-1]


def get_block_hash(node, conn, params):
    return node.index.header_index[params[0]]


def get_block_header(node, conn, params):
    block_hash = bytes.fromhex(params[0])
    block_info = node.index.get_block_info(block_hash)
    header = header = block_info.header
    out = header.to_dict()
    out["hash"] = header.hash

    # TODO: fix if is not in main chain
    height = node.index.header_index.index(block_hash)
    out["height"] = height
    out["confirmations"] = len(node.index.header_index) - height
    if height > 0:
        out["previousblockhash"] = node.index.header_index[height - 1]
    if height < len(node.index.header_index) - 1:
        out["nextblockhash"] = node.index.header_index[height + 1]
    out["chainwork"] = block_info.chainwork

    return out


def get_peer_info(node, conn, _):
    out = []
    for id, p2p_conn in node.p2p_manager.connections.items():
        if p2p_conn.status == P2pConnStatus.Connected:

            addr = p2p_conn.client.getpeername()
            addrbind = p2p_conn.client.getsockname()
            addrlocal_ip = p2p_conn.version_message.addr_from.ip.ipv4_mapped or addrbind[0]
            conn_dict = {
                "id": id,
                "addr": f"{addr[0]}:{addr[1]}",
                "addrbind": f"{addrbind[0]}:{addrbind[1]}",
                "addrlocal": f"{addrlocal_ip}:{addrbind[1]}",
            }
            out.append(conn_dict)

    return out


def get_connection_count(node, conn, _):
    return len(node.p2p_manager.connections)


def stop(node, conn, _):
    node.stop()
    return "Btclib node stopping"


callbacks = {
    "getbestblockhash": get_best_block_hash,
    "getblockhash": get_block_hash,
    "getblockheader": get_block_header,
    "getpeerinfo": get_peer_info,
    "getconnectioncount": get_connection_count,
    "stop": stop,
}
