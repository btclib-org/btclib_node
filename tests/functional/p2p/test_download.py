import time

import pytest

from btclib_node import Node
from btclib_node.chains import RegTest
from btclib_node.config import Config
from btclib_node.constants import NodeStatus
from btclib_node.main import update_chain
from tests.helpers import generate_random_chain, get_random_port


@pytest.mark.run(order=1)
def test_download(tmp_path):

    length = 3000
    chain = generate_random_chain(length, RegTest().genesis.hash)
    headers = [block.header for block in chain]

    download_nodes = []
    for x in range(10):
        download_nodes.append(
            Node(
                config=Config(
                    chain="regtest",
                    data_dir=tmp_path / f"node{x}",
                    p2p_port=get_random_port(),
                    allow_rpc=False,
                )
            )
        )

    for node in download_nodes:
        node.status = NodeStatus.HeaderSynced
        for x in range(0, length, 2000):
            node.index.add_headers(headers[x : x + 2000])
        for x in node.index.header_dict:
            block_info = node.index.get_block_info(x)
            block_info.downloaded = True
            node.index.insert_block_info(block_info)
        for block in chain:
            node.block_db.add_block(block)
        for x in range(len(chain)):
            update_chain(node)
        assert node.status == NodeStatus.BlockSynced
        node.start()

    main_node = Node(
        config=Config(
            chain="regtest",
            data_dir=tmp_path / "main",
            p2p_port=get_random_port(),
            allow_rpc=False,
            # debug=True,
        )
    )
    main_node.start()
    time.sleep(0.01)
    for node in download_nodes:
        main_node.p2p_manager.connect(("0.0.0.0", node.p2p_port))
        time.sleep(0.25)

    while True:
        time.sleep(0.001)
        if len(main_node.index.active_chain) == length + 1:
            break

    time.sleep(1)

    assert main_node.status == NodeStatus.BlockSynced

    main_node.stop()
    main_node.join()
    for node in download_nodes:
        node.stop()
        node.join()
