import os
from dataclasses import dataclass

import plyvel
from btclib import varint
from btclib.blocks import BlockHeader
from btclib.utils import bytesio_from_binarydata


@dataclass
class BlockStatus:
    header: BlockHeader
    index: int
    downloaded: bool = False

    @classmethod
    def deserialize(cls, data):
        stream = bytesio_from_binarydata(data)
        header = BlockHeader.deserialize(stream)
        index = varint.decode(stream)
        downloaded = bool(int.from_bytes(stream.read(1), "little"))
        return cls(header, index, downloaded)

    def serialize(self):
        out = self.header.serialize()
        out += varint.encode(self.index)
        out += int(self.downloaded).to_bytes(1, "little")
        return out


# TODO: currently if does not support blockchain reorganizations
class BlockIndex:
    def __init__(self, data_dir, chain):
        data_dir = os.path.join(data_dir, "index")
        os.makedirs(data_dir, exist_ok=True)
        self.db = plyvel.DB(data_dir, create_if_missing=True)

        genesis = chain.genesis
        genesis_status = BlockStatus(genesis, 0, True)

        self.header_dict = {genesis.hash: genesis_status}

        # the actual block chain; it contains only valid blocks
        self.active_chain = [genesis_status]

        # blocks that are waiting to be connected to the active chain
        self.block_candidates = []

        # blocks that have an anchestor missing
        self.unlinked_blocks = {}

        # list all header hashes, even if not already checked
        # needed for the block locators and to know which block to download
        self.header_index = [genesis.hash]

        # the first 1024 block window with at least one block not downloaded
        self.download_index = 0

        self.init_from_db()

    def init_from_db(self):
        pass
        # for key, value in self.db:
        #     self.header_dict[key.hex()] = BlockStatus.deserialize(value)

    def update(self):
        pass

    def insert_header_status(self, header_status):
        self.header_dict[header_status.header.hash] = header_status
        # key = b"b" + bytes.fromhex(header_status.header.hash)
        # value = header_status.serialize()
        # self.db.put(key, value)
        # self.update()

    def get_header_status(self, hash):
        return self.header_dict[hash]

    def add_headers(self, headers):
        added = False  # flag that signals if there is a new header in this message
        for header in headers:
            if header.hash in self.header_dict:
                continue
            if header.previousblockhash not in self.header_dict:
                continue
            added = True
            previous_block = self.get_header_status(header.previousblockhash)
            block_status = BlockStatus(header, previous_block.index + 1, False)
            self.insert_header_status(block_status)

            # TODO: rewrite to support reorgs
            if header.previousblockhash == self.header_index[-1]:
                self.header_index.append(header.hash)
        return added

    # return a list of blocks that have to be downloaded
    def get_download_candidates(self):
        candidates = []
        i = self.download_index
        downloadable = self.header_index[i * 1024 : (i + 1) * 1024]
        for header in downloadable:
            if not self.get_header_status(header).downloaded:
                candidates.append(header)
        if not candidates and len(self.header_index) > self.download_index * 1024:
            self.download_index += 1
            return self.get_download_candidates()
        else:
            return candidates

    # return a list of block hashes looking at the current best chain
    def get_block_locator_hashes(self):
        i = 1
        step = 1
        block_locators = []
        while True:
            if i > len(self.header_index):
                break
            block_locators.append(self.header_index[-i])
            if i >= 10:
                step *= 2
            i += step
        if self.header_index[0] not in block_locators:
            block_locators.append(self.header_index[0])
        return block_locators

    def get_headers_from_locators(self, block_locators, stop):
        output = []
        for block_locator in block_locators:
            if block_locator not in self.header_index:
                continue
            start = self.header_index.index(block_locator)
            output = self.header_index[start + 1 :]
            if stop in self.header_index:
                end = self.header_index.index(stop)
                output = output[: end + 1]
            output = output[:2000]
            break
        return [self.get_header_status(x).header for x in output]
