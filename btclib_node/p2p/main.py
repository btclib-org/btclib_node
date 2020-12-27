import traceback

from btclib_node.p2p.callbacks import callbacks, handshake_callbacks
from btclib_node.p2p.constants import ConnectionStatus


def handle_p2p_handshake(node):
    msg_type, msg, conn_id = node.p2p_manager.handshake_messages.popleft()
    if conn_id in node.p2p_manager.connections:
        conn = node.p2p_manager.connections[conn_id]
        print(msg_type, conn_id)
        try:
            if msg_type in handshake_callbacks:
                handshake_callbacks[msg_type](node, msg, conn)
        except Exception:
            conn.stop()
            traceback.print_exc()


def handle_p2p(node):
    msg_type, msg, conn_id = node.p2p_manager.messages.popleft()
    if conn_id in node.p2p_manager.connections:
        conn = node.p2p_manager.connections[conn_id]
        print(msg_type, conn_id)
        try:
            if msg_type in callbacks:
                if conn.status > ConnectionStatus.Version:
                    callbacks[msg_type](node, msg, conn)
                else:
                    conn.stop()
        except Exception:
            conn.stop()
            traceback.print_exc()
