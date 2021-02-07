import time

from btclib_node.constants import NodeStatus
from btclib_node.index import BlockStatus


# TODO: we have to check it there are more blocks ahead to put into the header index
def update_header_index(index, to_add):
    for block_hash in to_add:
        if block_hash not in index.header_index:
            index.header_index = index.active_chain[:]


# TODO: support for failed updates
def update_chain(node):
    if node.status < NodeStatus.HeaderSynced:
        return

    index = node.index
    if not index.get_first_candidate():
        node.status = NodeStatus.BlockSynced
        return

    to_add, to_remove = index.get_fork_details(index.get_first_candidate().header.hash)
    for block_hash in to_add:
        if not index.get_block_info(block_hash).downloaded:
            return

    for block_hash in to_remove:
        # remove block
        pass
    for block_hash in to_add:
        # add block
        # success = try_add_block()
        success = True
        if success:
            block_info = index.get_block_info(block_hash)
            block_info.status = BlockStatus.valid
            index.insert_block_info(block_info)
        else:
            block_info = index.get_block_info(block_hash)
            block_info.status = BlockStatus.invalid
            index.insert_block_info(block_info)
            break

    if success:
        for block_hash in to_remove:
            index.active_chain.remove(block_hash)
            block_info = index.get_block_info(block_hash)
            block_info.status = BlockStatus.valid
            index.insert_block_info(block_info)
        for block_hash in to_add:
            index.active_chain.append(block_hash)
            block_info = index.get_block_info(block_hash)
            block_info.status = BlockStatus.in_active_chain
            index.insert_block_info(block_info)
        a = time.time()
        index.prune_block_candidates()
        print(time.time() - a)
        update_header_index(index, to_add)
    else:
        pass

    if not index.get_first_candidate():
        node.status = NodeStatus.BlockSynced
