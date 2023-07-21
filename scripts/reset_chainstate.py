from btclib_node.chainstate import Chainstate
from btclib_node.config import Config
from btclib_node.index import BlockIndex, BlockInfo, BlockStatus
from btclib_node.log import Logger

config = Config(
    chain="mainnet", data_dir=".btclib", p2p_port=30000, rpc_port=30001, debug=True
)
logger = Logger(config.data_dir / "history.log", config.debug)
blockindex = BlockIndex(config.data_dir, config.chain, logger)
chainstate = Chainstate(config.data_dir, logger)

for block_hash in blockindex.active_chain[1:]:
    x = BlockInfo.deserialize(blockindex.db.get(b"b" + block_hash))
    x.status = BlockStatus.valid_header
    blockindex.db.put(b"b" + block_hash, x.serialize())

with chainstate.db.write_batch():
    for key, _ in chainstate.db:
        chainstate.db.delete(key)