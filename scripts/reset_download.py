from btclib_node.block_db import BlockDB
from btclib_node.config import Config
from btclib_node.index import BlockIndex, BlockInfo, BlockStatus
from btclib_node.log import Logger

config = Config(
    chain="mainnet", data_dir=".btclib", p2p_port=30000, rpc_port=30001, debug=True
)
logger = Logger(config.data_dir / "history.log", config.debug)
blockdb = BlockDB(config.data_dir, logger)
blockindex = BlockIndex(config.data_dir, config.chain, logger)

fix_idx = 440599

for block_hash in blockindex.active_chain[fix_idx + 1 :]:
    block_info = blockindex.get_block_info(block_hash)
    block_info.downloaded = False
    block_info.status = BlockStatus.valid_header
    blockindex.insert_block_info(block_info)
    blockdb.db.delete(b"b" + block_hash)
