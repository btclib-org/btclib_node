from collections import Counter

from btclib_node.constants import NodeStatus
from btclib_node.p2p.messages.getdata import Getdata


def block_download(node):
    if node.status < NodeStatus.HeaderSynced:
        return

    block_index = node.chainstate.block_index

    if not node.download_window:
        node.download_window = block_index.get_download_candidates()
    node.download_window = [
        x for x in node.download_window if not block_index.get_block_info(x).downloaded
    ]
    if not node.download_window:
        return

    connections = list(node.p2p_manager.connections.values())
    pending = []
    skip = True
    for conn in connections:
        conn_queue = conn.download_queue
        new_queue = []
        for header in conn_queue:
            if not block_index.get_block_info(header).downloaded:
                new_queue.append(header)
        conn.download_queue = new_queue
        pending.extend(new_queue)
        if not new_queue:
            skip = False
    if skip:
        return

    waiting = [header for header in node.download_window if header not in pending]
    pending = [x[0] for x in Counter(pending).most_common()[::-1]]

    for conn in connections:
        if conn.block_download_queue == []:
            if waiting:
                new = waiting[:16]
                waiting = waiting[16:]
            elif pending:
                new = pending[:4]
                pending = pending[4:]
            else:
                return
            conn.download_queue = new
            conn.send(Getdata([(0x40000002, hash) for hash in new]))
