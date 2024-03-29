from btclib_node import Node
from btclib_node.chains import RegTest
from btclib_node.config import Config
from btclib_node.constants import NodeStatus, P2pConnStatus
from tests.helpers import (
    generate_random_chain,
    generate_random_transaction,
    get_random_port,
    local_addr,
    wait_until,
)


def test_send_tx(tmp_path):
    node1 = Node(
        config=Config(
            chain="regtest",
            data_dir=tmp_path / "node1",
            p2p_port=get_random_port(),
            allow_rpc=False,
        )
    )
    node2 = Node(
        config=Config(
            chain="regtest",
            data_dir=tmp_path / "node2",
            p2p_port=get_random_port(),
            allow_rpc=False,
        )
    )
    node1.start()
    node2.start()

    wait_until(lambda: node1.p2p_manager.is_alive())
    wait_until(lambda: node2.p2p_manager.is_alive())

    # Add one block
    block = generate_random_chain(1, RegTest().genesis.hash)[0]
    for node in (node1, node2):
        block_index = node.chainstate.block_index
        node.chainstate.block_index.add_headers([block.header])
        node.status = NodeStatus.HeaderSynced
        node.block_db.add_block(block)
        block_info = block_index.get_block_info(block.header.hash)
        block_info.downloaded = True
        block_index.insert_block_info(block_info)
        wait_until(lambda: len(block_index.active_chain) == 2)

    node2.p2p_manager.connect(local_addr(node1.p2p_port))
    wait_until(lambda: len(node1.p2p_manager.connections))
    connection = node1.p2p_manager.connections[0]
    wait_until(lambda: connection.status == P2pConnStatus.Connected)
    connection = node2.p2p_manager.connections[0]
    wait_until(lambda: connection.status == P2pConnStatus.Connected)

    tx = generate_random_transaction(block.transactions[0].id)

    assert node1.mempool.size == 0

    node2.p2p_manager.broadcast_raw_transaction(tx)

    try:
        wait_until(lambda: node1.mempool.size)
    finally:
        node1.stop()
        node2.stop()
        node1.join()
        node2.join()
