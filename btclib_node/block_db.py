from dataclasses import dataclass
from typing import List, Tuple

from btclib.blocks import Block
from btclib.tx_in import OutPoint
from btclib.tx_out import TxOut


class BlockDB:
    def __init__(self, data_dir):
        data_dir = data_dir / "blocks"
        data_dir.mkdir(exist_ok=True, parents=True)
        self.cache = {}
        self.rev_cache = {}

    def close(self):
        pass

    # TODO: store on disk
    def add_block(self, block):
        self.cache[block.header.hash] = block

    def add_rev_block(self, rev_block):
        self.rev_cache[rev_block.hash] = rev_block

    def get_block(self, hash):
        if hash in self.cache:
            return self.cache[hash]
        return None

    def get_rev_block(self, hash):
        if hash in self.rev_caches:
            return self.rev_cache[hash]
        return None


@dataclass
class RevBlock:
    hash: str
    to_add: List[Tuple[OutPoint, TxOut]]
    to_remove: List[OutPoint]
