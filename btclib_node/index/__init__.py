import os
import enum
from dataclasses import dataclass

import plyvel
from btclib import varint
from btclib.blocks import BlockHeader
from btclib.utils import bytesio_from_binarydata


class BlockStatus(enum.IntEnum):
    valid_header = 1
    invalid = 2
    valid = 3
    in_active_chain = 4


@dataclass
class BlockInfo:
    header: BlockHeader
    index: int
    status: BlockStatus
    downloaded: bool = False

    @classmethod
    def deserialize(cls, data):
        stream = bytesio_from_binarydata(data)
        header = BlockHeader.deserialize(stream)
        index = varint.decode(stream)
        status = BlockStatus.from_bytes(stream.read(1), "little")
        downloaded = bool(int.from_bytes(stream.read(1), "little"))
        return cls(header, index, status, downloaded)

    def serialize(self):
        out = self.header.serialize()
        out += varint.encode(self.index)
        out += self.status.to_bytes(1, "little")
        out += int(self.downloaded).to_bytes(1, "little")
        return out


# TODO: currently if does not support blockchain reorganizations
class BlockIndex:
    def __init__(self, data_dir, chain):
        data_dir = os.path.join(data_dir, "index")
        os.makedirs(data_dir, exist_ok=True)
        self.db = plyvel.DB(data_dir, create_if_missing=True)

        genesis = chain.genesis
        genesis_status = BlockInfo(genesis, 0, BlockStatus.in_active_chain, True)

        self.header_dict = {genesis.hash: genesis_status}

        # the actual block chain; it contains only valid blocks
        self.active_chain = [genesis.hash]

        # blocks that are waiting to be connected to the active chain
        self.download_candidates = []

        # blocks that have an anchestor missing
        self.unlinked_blocks = {}

        # list all header hashes, even if not already checked
        # needed for the block locators
        self.header_index = [genesis.hash]

        self.init_from_db()

    def init_from_db(self):
        pass
        # for key, value in self.db:
        #     self.header_dict[key.hex()] = BlockInfo.deserialize(value)
        # self.update_download_candidates()
        # self.update_header_index()

    def generate_download_candidates(self):
        pass

    def update_download_candidates(self):
        pass

    def generate_header_index(self):
        pass

    # TODO: rewrite to support reorgs
    def update_header_index(self, header):
        if header.previousblockhash == self.header_index[-1]:
            self.header_index.append(header.hash)

    def insert_block_info(self, block_info):
        self.header_dict[block_info.header.hash] = block_info
        # key = b"b" + bytes.fromhex(block_info.header.hash)
        # value = block_info.serialize()
        # self.db.put(key, value)

    def get_block_info(self, hash):
        return self.header_dict[hash]

    # returns the active chain and the forked chain from the common anchestor
    def get_fork_details(self, header_hash):
        fork = [header_hash]
        while True:
            block_info = self.get_block_info(header_hash)
            header_hash = block_info.header.previousblockhash
            if header_hash in self.active_chain:
                anchestor_index = self.active_chain.index(header_hash)
                break
            else:
                fork.append(header_hash)
        main = self.active_chain[anchestor_index + 1 :]
        return fork, main

    def add_headers(self, headers):
        added = False  # flag that signals if there is a new header in this message
        for header in headers:
            if header.hash in self.header_dict:
                continue
            if header.previousblockhash not in self.header_dict:
                continue
            added = True
            previous_block = self.get_block_info(header.previousblockhash)
            index = previous_block.index + 1
            block_info = BlockInfo(header, index, BlockStatus.valid_header)
            self.insert_block_info(block_info)
            self.update_header_index(header)

            # TODO: use total work instead of lenght
            if index > self.get_block_info(self.active_chain[-1]).index:
                self.download_candidates.append(header.hash)

        return added

    # return a list of blocks that have to be downloaded
    def get_download_candidates(self):
        candidates = []
        i = -1
        while len(candidates) < 1024:
            i += 1
            if i >= len(self.download_candidates):
                break
            candidate = self.download_candidates[i]
            if candidate not in candidates:
                new_candidates = [candidate]
                while True:
                    block_info = self.get_block_info(candidate)
                    candidate = block_info.header.previousblockhash
                    if candidate in candidates or candidate in self.active_chain:
                        break
                    if not self.get_header_status(candidate).downloaded:
                        new_candidates.append(candidate)
                candidates = candidates + new_candidates[::-1]
        return candidates[:1024]

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
        return [self.get_block_info(x).header for x in output]
