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

    # TODO: store on disk
    def add_block(self, block):
        self.cache[block.header.hash] = block

    def add_rev_block(self, rev_block):
        self.rev_cache[rev_block.hash] = rev_block

    def get_block(self, hash):
        return self.cache[hash]

    def get_rev_block(self, hash):
        return self.rev_cache[hash]


@dataclass
class RevBlock:
    hash: str
    to_add: List[Tuple[OutPoint, TxOut]]
    to_remove: List[OutPoint]
