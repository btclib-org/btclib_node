import plyvel
from btclib.tx.tx_in import OutPoint
from btclib.tx.tx_out import TxOut

from btclib_node.block_db import RevBlock

from .block_index import BlockIndex
from .utxo_index import UtxoIndex


class Chainstate:
    def __init__(self, data_dir, chain, logger):
        data_dir = data_dir / "chainstate"
        data_dir.mkdir(exist_ok=True, parents=True)
        self.db = plyvel.DB(str(data_dir), create_if_missing=True)

        self.block_index = BlockIndex(self.db, chain, logger)
        self.utxo_index = UtxoIndex(self.db, logger)

        self.logger = logger

    def close(self):
        self.logger.info("Closing Chainstate db")
        self.db.close()
