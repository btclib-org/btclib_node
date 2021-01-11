from btclib_node.constants import NodeStatus


# TODO: support for reogranizations
def update_chain(node):
    index = node.index
    if not index.download_candidates:
        return

    to_add, to_remove = index.get_fork_details(index.download_candidates[0])
    for block_hash in to_add:
        if not index.get_block_info(block_hash).downloaded:
            return

    index.active_chain.extend(to_add)

    # TODO: update download candidates
    for block in to_add:
        if block in index.download_candidates:
            index.download_candidates.remove(block)

    # TODO: update header index

    if not index.download_candidates:
        node.status = NodeStatus.BlockSynced
