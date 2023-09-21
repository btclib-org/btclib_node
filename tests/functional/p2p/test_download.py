import shutil
import time

import pytest

from btclib_node import Node
from btclib_node.chains import RegTest
from btclib_node.config import Config
from btclib_node.constants import NodeStatus
from btclib_node.main import update_chain
from tests.helpers import generate_random_chain, get_random_port, local_addr, wait_until


@pytest.mark.run(order=1)
def test_download(tmp_path):

    length = 3000
    chain = generate_random_chain(length, RegTest().genesis.hash)
    headers = [block.header for block in chain]

    bootstrap_node = Node(
        config=Config(
            chain="regtest",
            data_dir=tmp_path / "node0",
            p2p_port=get_random_port(),
            allow_rpc=False,
        )
    )
    bootstrap_node.status = NodeStatus.HeaderSynced
    bootstrap_block_index = bootstrap_node.chainstate.block_index
    for x in range(0, length, 2000):
        bootstrap_block_index.add_headers(headers[x : x + 2000])
    for x in bootstrap_block_index.header_dict:
        block_info = bootstrap_block_index.get_block_info(x)
        block_info.downloaded = True
        bootstrap_block_index.insert_block_info(block_info)
    for block in chain:
        bootstrap_node.block_db.add_block(block)
    for x in range(len(chain)):
        update_chain(bootstrap_node)
    assert bootstrap_node.status == NodeStatus.BlockSynced
    bootstrap_node.start()

    download_nodes = [bootstrap_node]
    for x in range(1, 10):
        shutil.copytree(tmp_path / "node0", tmp_path / f"node{x}")
        node = Node(
            config=Config(
                chain="regtest",
                data_dir=tmp_path / f"node{x}",
                p2p_port=get_random_port(),
                allow_rpc=False,
            )
        )
        node.start()
        wait_until(lambda: node.p2p_manager.is_alive())
        download_nodes.append(node)

    main_node = Node(
        config=Config(
            chain="regtest",
            data_dir=tmp_path / "main",
            p2p_port=get_random_port(),
            allow_rpc=False,
        )
    )
    main_node.start()
    wait_until(lambda: main_node.p2p_manager.is_alive())

    for node in download_nodes:
        main_node.p2p_manager.connect(local_addr(node.p2p_port))
        time.sleep(0.25)

    block_index = main_node.chainstate.block_index
    wait_until(lambda: len(block_index.active_chain) == length + 1, timeout=20)
    wait_until(lambda: main_node.status == NodeStatus.BlockSynced, timeout=0.5)

    main_node.stop()
    main_node.join()
    for node in download_nodes:
        node.stop()
        node.join()
