from btclib_node.rpc.callbacks import callbacks


def get_connection(manager, id):
    try:
        conn = manager.connections[id]
        return conn
    except Exception:
        return None


def handle_rpc(node):
    msg_type, msg, conn_id = node.rpc_manager.messages.popleft()
    conn = get_connection(node.rpc_manager, conn_id)
    if not conn:
        conn.close()
        return
    if msg_type not in callbacks.keys():
        conn.send(None, {"code": -32601, "message": "Method not found"})
        return
    try:
        callbacks[msg_type](node, msg, conn)
    except Exception as e:
        print(e)
        conn.close()
        return
