from btclib_node.block_db import BlockDB
from btclib_node.chainstate import Chainstate
from btclib_node.chainstate.block_index import BlockIndex, BlockInfo, BlockStatus
from btclib_node.config import Config
from btclib_node.log import Logger

config = Config(
    chain="mainnet",
    data_dir=".btclib",
)
logger = Logger(debug=True)
blockdb = BlockDB(config.data_dir, logger)
chainstate = Chainstate(config.data_dir, config.chain, logger)
blockindex = chainstate.block_index

fix_idx = 406315

for block_hash in blockindex.active_chain[fix_idx + 1 :]:
    block_info = blockindex.get_block_info(block_hash)
    block_info.downloaded = False
    block_info.status = BlockStatus.valid_header
    blockindex.insert_block_info(block_info)
    blockdb.db.delete(b"b" + block_hash)
