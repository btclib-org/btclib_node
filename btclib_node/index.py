from dataclasses import dataclass

from btclib.blocks import BlockHeader


@dataclass
class BlockStatus:
    header: BlockHeader
    downloaded: bool = False


# TODO: currently if does not support blockchain reorganizations
class BlockIndex:
    def __init__(self, data_dir, chain):
        genesis = chain.genesis
        self.headers = {genesis.hash: BlockStatus(genesis, True)}
        self.index = [genesis.hash]

    def add_headers(self, headers):
        added = False  # flag that tells there is a new header in this message
        for header in headers:
            hash = header.hash
            if hash not in self.headers:
                added = True
                block_status = BlockStatus(header, False)
                self.headers[header.hash] = block_status
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
            if i > len(self.index):
                break
            block_locators.append(self.index[-i])
            if i >= 10:
                step *= 2
            i += step
        if self.index[0] not in block_locators:
            block_locators.append(self.index[0])
        return block_locators
