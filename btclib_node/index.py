from dataclasses import dataclass
from typing import Dict, List

from btclib.blocks import BlockHeader


# TODO: currently if does not support blockchain reorganizations
@dataclass
class BlockIndex:
    headers: Dict[str, BlockHeader]
    index: List[str]

    def add_headers(self, headers):
        added = False  # flag that tells there is a new header in this message
        for header in headers:
            hash = header.hash
            if hash not in self.headers:
                added = True
                self.headers[header.hash] = header
                if header.previousblockhash == self.index[-1]:
                    self.index.append(header.hash)
        return added

    def get_headers(self, block_locators, stop):
        return []

    # return a list of block hashes looking at the current best chain
    def get_block_locator_hashes(self):
        i = 1
        step = 1
        block_locators = []
        while True:
            block_locators.append(self.index[-i])
            if i >= 10:
                step *= 2
            i += step
            if i > len(self.index):
                return block_locators
