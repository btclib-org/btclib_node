import time

from btclib_node.constants import NodeStatus
from btclib_node.index import BlockStatus


def update_block_status(index, hash, status):
    block_info = index.get_block_info(hash)
    block_info.status = status
    index.insert_block_info(block_info)


# TODO: we have to check it there are more blocks ahead to put into the header node.index
def update_header_index(index):
    pass


# TODO: support for failed updates
def update_chain(node):
    if node.status < NodeStatus.HeaderSynced:
        return

    first_candidate = node.index.get_first_candidate()
    if not first_candidate:
        node.status = NodeStatus.BlockSynced
        return
    to_add, to_remove = node.index.get_fork_details(first_candidate.header.hash)

    for hash in to_add:
        if not node.index.get_block_info(hash).downloaded:
            return
    to_add = [node.block_db.get_block(hash) for hash in to_add]
    to_remove = [node.block_db.get_rev_block(hash) for hash in to_remove]

    for rev_block in to_remove:
        # remove block
        pass
    for block in to_add:
        # add block
        # success = try_add_block()
        success = True
        if success:
            update_block_status(node.index, block.header.hash, BlockStatus.valid)
        else:
            update_block_status(node.index, block.header.hash, BlockStatus.invalid)
            break

    if success:
        for rev_block in to_remove:
            node.index.active_chain.remove(rev_block.hash)
            node.chainstate.apply_rev_block(rev_block)
            update_block_status(node.index, rev_block.hash, BlockStatus.valid)
        for block in to_add:
            node.index.active_chain.append(block.header.hash)
            rev_block = node.chainstate.add_block(block)
            node.block_db.add_rev_block(rev_block)
            update_block_status(
                node.index, block.header.hash, BlockStatus.in_active_chain
            )

        a = time.time()
        node.index.prune_block_candidates()
        node.logger.debug(f"Time taken to add block: {time.time() - a}")

    else:
        update_header_index(node.index)

    if not node.index.get_first_candidate():
        node.status = NodeStatus.BlockSynced
