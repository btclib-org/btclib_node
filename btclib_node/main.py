from btclib_node.constants import NodeStatus
from btclib_node.index import BlockStatus
from btclib_node.interpreter import check_transactions
from btclib_node.p2p.messages.filters import Filterclear


def update_block_status(index, hash, status):
    block_info = index.get_block_info(hash)
    block_info.status = status
    index.insert_block_info(block_info)


# TODO: we have to check it there are more blocks ahead to invalidate
def update_header_index(index):
    pass


def finish_sync(node):
    if node.status == NodeStatus.BlockSynced:
        return
    node.status = NodeStatus.BlockSynced
    for conn in list(node.p2p_manager.connections.values()):
        conn.send(Filterclear())


# TODO: support for failed updates
def update_chain(node):

    if node.status < NodeStatus.HeaderSynced:
        return

    first_candidate = node.index.get_first_candidate()
    if not first_candidate:
        return finish_sync(node)

    to_add_hash, to_remove_hash = node.index.get_fork_details(
        first_candidate.header.hash
    )

    for hash in to_add_hash:
        if not node.index.get_block_info(hash).downloaded:
            # FIXME: naive way to prevent node from blocking due to missing stale block
            # node.index.block_candidates.insert(100, node.index.block_candidates.popleft())
            return

    node.logger.debug("Start getting blocks")

    to_add = [node.block_db.get_block(hash) for hash in to_add_hash]
    to_remove = [node.block_db.get_rev_block(hash) for hash in to_remove_hash]

    node.logger.debug("Got all blocks")
    node.logger.debug("Start chainstate test")

    success = True
    generated_rev_patches = []
    try:
        for rev_block in to_remove:
            node.chainstate.apply_rev_block(rev_block)
        for hash, block in zip(to_add_hash, to_add):
            transactions, rev_patch = node.chainstate.add_block(block)
            indx = node.index.get_block_info(hash).index
            check_transactions(transactions, indx, node)
            generated_rev_patches.append(rev_patch)
            update_block_status(node.index, block.header.hash, BlockStatus.valid)
    except Exception:
        node.logger.exception("Exception occurred")
        success = False
    finally:
        if success:
            node.logger.debug("Start chainstate finalize")
            node.chainstate.finalize()
            node.logger.debug("End chainstate finalize")
        else:
            node.logger.debug("Start chainstate rollback")
            node.chainstate.rollback()
            node.logger.debug("End chainstate rollback")

    node.logger.debug("Start updating index")

    if success:
        for rev_block in to_remove:

            node.index.remove_from_active_chain(rev_block.hash)
            update_block_status(node.index, rev_block.hash, BlockStatus.valid)
            node.logger.debug(f"Removed block {rev_block.hash.hex()}")

            block = node.block_db.get_block(rev_block.hash)
            for tx in block.transactions[1:]:
                node.mempool.add_tx(tx)

        for rev_block, block in zip(generated_rev_patches, to_add):

            block_hash = block.header.hash
            node.index.add_to_active_chain(block_hash)
            update_block_status(node.index, block_hash, BlockStatus.in_active_chain)
            node.logger.debug(f"Added block {block.header.hash.hex()}")

            node.block_db.add_rev_block(rev_block)

            if node.status == NodeStatus.BlockSynced:
                for tx in block.transactions:
                    node.mempool.remove_tx(tx.id)

    else:
        update_header_index(node.index)

    node.logger.debug("Finished main\n")

    if not node.index.get_first_candidate():
        return finish_sync(node)
