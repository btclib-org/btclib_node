def get_best_block_hash(node, conn, _):
    return node.index.header_index[-1]


def get_block_hash(node, conn, params):
    return node.index.header_index[params[0]]


def get_block_header(node, conn, params):
    block_info = node.index.get_block_info(params[0])
    header = header = block_info.header
    out = header.to_dict()
    out["hash"] = header.hash

    # TODO: fix if is not in main chain
    height = node.index.header_index.index(params[0])
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
        try:
            conn_dict = {}
            conn_dict["id"] = id
            addr = (
                f"{p2p_conn.client.getpeername()[0]}:{p2p_conn.client.getpeername()[1]}"
            )
            conn_dict["addr"] = addr
            addrbind = (
                f"{p2p_conn.client.getsockname()[0]}:{p2p_conn.client.getsockname()[1]}"
            )
            conn_dict["addrbind"] = addrbind
            out.append(conn_dict)
        except OSError:
            pass
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
