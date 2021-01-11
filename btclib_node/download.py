from collections import Counter

from btclib_node.constants import NodeStatus
from btclib_node.p2p.messages.getdata import Getdata


def block_download(node):
    if node.status >= NodeStatus.HeaderSynced:

        if not node.download_window:
            node.download_window = node.index.get_download_candidates()
        if not node.download_window:
            return

        node.download_window = [
            x
            for x in node.download_window
            if not node.index.get_block_info(x).downloaded
        ]

        connections = node.p2p_manager.connections.values()
        pending = []
        exit = True
        for conn in connections:
            conn_queue = conn.block_download_queue
            new_queue = []
            for header in conn_queue:
                if not node.index.get_block_info(header).downloaded:
                    new_queue.append(header)
            conn.block_download_queue = new_queue
            pending.extend(new_queue)
            if not new_queue:
                exit = False
        if exit:
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
                conn.block_download_queue = new
                conn.send(Getdata([(0x40000002, hash) for hash in new]))
