from dataclasses import dataclass, field
from typing import Dict, List

from btclib.blocks import BlockHeader

genesis_block_hash = "000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8ce26f"


@dataclass
class BlockStatus:
    header: BlockHeader
    downloaded: bool = False


# TODO: currently if does not support blockchain reorganizations
@dataclass
class BlockIndex:
    headers: Dict[str, BlockStatus] = field(default_factory=lambda: {})
    index: List[str] = field(default_factory=lambda: [])

    def add_headers(self, headers):
        added = False  # flag that tells there is a new header in this message
        for header in headers:
            hash = header.hash
            if hash not in self.headers:
                added = True
                block_status = BlockStatus(header, False)
                self.headers[header.hash] = block_status
                if not len(self.index):
                    if header.previousblockhash == genesis_block_hash:
                        self.index.append(header.hash)
                elif header.previousblockhash == self.index[-1]:
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
            if i > len(self.index):
                break
            block_locators.append(self.index[-i])
            if i >= 10:
                step *= 2
            i += step
        if genesis_block_hash not in block_locators:
            block_locators.append(genesis_block_hash)
        return block_locators
