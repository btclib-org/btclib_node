import time

from btclib_node.chainstate import ChainstateSnapshot
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
    # print(to_add, to_remove)
    for hash in to_add:
        if not node.index.get_block_info(hash).downloaded:
            return
    to_add = [node.block_db.get_block(hash) for hash in to_add]
    to_remove = [node.block_db.get_rev_block(hash) for hash in to_remove]

    chainstate_snapshot = ChainstateSnapshot(node.chainstate)
    for rev_block in to_remove:
        chainstate_snapshot.apply_rev_block(rev_block)
    for block in to_add:
        try:
            transactions = chainstate_snapshot.add_block(block)
            # script_engine.validate(transactions)
            success = True
        except Exception:
            node.logger.exception("Exception occurred")
            node.logger.debug(block)
            node.logger.debug(block.header.hash)
            success = False
        if success:
            update_block_status(node.index, block.header.hash, BlockStatus.valid)
        else:
            update_block_status(node.index, block.header.hash, BlockStatus.invalid)
            break

    if success:
        for rev_block in to_remove:
            node.index.remove_from_active_chain(rev_block.hash)
            node.chainstate.apply_rev_block(rev_block)
            update_block_status(node.index, rev_block.hash, BlockStatus.valid)
        for block in to_add:
            node.index.add_to_active_chain(block.header.hash)
            rev_block = node.chainstate.add_block(block)
            node.block_db.add_rev_block(rev_block)
            update_block_status(
                node.index, block.header.hash, BlockStatus.in_active_chain
            )

        a = time.time()
        node.logger.debug(f"Time taken to add block: {time.time() - a}")

    else:
        update_header_index(node.index)

    if not node.index.get_first_candidate():
        node.status = NodeStatus.BlockSynced
