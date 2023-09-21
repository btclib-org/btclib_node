import time
from collections import Counter

from btclib_node.constants import NodeStatus
from btclib_node.p2p.messages.getdata import Getdata, InventoryType


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
    current_index = len(block_index.active_chain) - 1
    download_index = block_index.get_block_info(node.download_window[0]).index
    # too much ahead with the download
    if download_index - current_index > 1024:
        return

    connections = list(node.p2p_manager.connections.values())
    if node.status < NodeStatus.BlockSynced:
        for conn in connections:
            if (
                time.time() - conn.last_block_timestamp > 120
                and not conn.pending_eviction
            ):
                conn.download_queue = []
                conn.pending_eviction = True
            if time.time() - conn.last_block_timestamp > 300:
                conn.stop()

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
    pending = [x[0] for x in Counter(pending).most_common()[::-1] if x[1] < 3]

    for conn in connections:
        if conn.download_queue == []:
            if waiting:
                new = waiting[:16]
                waiting = waiting[16:]
            elif pending:
                new = pending[:2]
                pending = pending[2:]
            else:
                return
            conn.download_queue = new
            conn.send(Getdata([(InventoryType.witness_block, hash) for hash in new]))
