import enum
import os
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

    # TODO: should be implemented in btclib
    @property
    def work(self):
        target = int.from_bytes(self.header.bits[-3:], "big")
        exp = pow(256, (self.header.bits[0] - 3))
        return int(256 ** 32 / target / exp)

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
        genesis_info = BlockInfo(genesis, 0, BlockStatus.in_active_chain, True)

        self.header_dict = {genesis.hash: genesis_info}

        # the actual block chain; it contains only valid blocks
        self.active_chain = [genesis.hash]

        # blocks that are waiting to be connected to the active chain
        self.block_candidates = []

        # list all header hashes, even if not already checked, needed for the block locators
        self.header_index = [genesis.hash]

        self.init_from_db()

    def init_from_db(self):
        for key, value in self.db:
            prefix, key = key[:1], key[1:]
            if prefix == b"b":
                self.header_dict[key.hex()] = BlockInfo.deserialize(value)
        self.generate_active_chain()
        self.generate_block_candidates()
        self.generate_header_index()

    def generate_active_chain(self):
        chain_dict = {}
        for block_hash, block_info in self.header_dict.items():
            if block_info.status == BlockStatus.in_active_chain:
                chain_dict[block_info.index] = block_hash
        for index in sorted(chain_dict.keys()):
            self.active_chain.append(chain_dict[index])
        del self.active_chain[0]  # TODO: ugly, done to prevent doubles in active chain

    def generate_block_candidates(self):
        block_candidates_set = set()
        active_chain_set = set(self.active_chain)
        sorted_dict = sorted(self.header_dict, key=lambda x: self.header_dict[x].index)
        for block_hash in sorted_dict:
            if block_hash in active_chain_set:
                continue
            block_info = self.get_block_info(block_hash)
            if block_info.status != BlockStatus.valid_header:
                continue
            header = block_info.header
            if (
                self.block_candidates
                and header.previousblockhash == self.block_candidates[-1]
            ):
                self.block_candidates.append(header.hash)
                block_candidates_set.add(header.hash)
            elif header.previousblockhash in block_candidates_set:
                self.block_candidates.append(header.hash)
                block_candidates_set.add(header.hash)
            elif self.more_work(header.hash):
                self.block_candidates.append(header.hash)
                block_candidates_set.add(header.hash)

    def generate_header_index(self):
        self.header_index = self.active_chain[:]
        sorted_dict = sorted(self.header_dict, key=lambda x: self.header_dict[x].index)
        for block_hash in sorted_dict:
            if block_hash in self.header_index:
                continue
            header = self.get_block_info(block_hash).header
            if header.previousblockhash == self.header_index[-1]:
                self.header_index.append(block_hash)
            elif self.more_work(block_hash, self.header_index):
                self.header_index.append(block_hash)

    # TODO: should use copy to preserve immutability
    def insert_block_info(self, block_info):
        new_block_info = block_info
        self.header_dict[block_info.header.hash] = new_block_info
        key = b"b" + bytes.fromhex(new_block_info.header.hash)
        value = new_block_info.serialize()
        self.db.put(key, value)

    # TODO: should use copy to preserve immutability
    def get_block_info(self, hash):
        return self.header_dict[hash]

    # returns the active chain and the forked chain from the common anchestor
    def get_fork_details(self, header_hash, chain=None):
        if not chain:
            chain = self.active_chain
        fork = [header_hash]
        while True:
            block_info = self.get_block_info(header_hash)
            header_hash = block_info.header.previousblockhash
            if header_hash in chain:
                anchestor_index = chain.index(header_hash)
                break
            else:
                fork.append(header_hash)
        main = chain[anchestor_index + 1 :]
        return fork, main

    # checks if the new header has more work than a chain
    def more_work(self, header_hash, chain=None):
        if not chain:
            chain = self.active_chain
        new, old = self.get_fork_details(header_hash, chain)
        old_work = 0
        for block_hash in old:
            old_work += self.get_block_info(header_hash).work
        new_work = 0
        for block_hash in new:
            new_work += self.get_block_info(header_hash).work
        return new_work > old_work

    def update_header_index(self, header):
        if header.previousblockhash == self.header_index[-1]:
            self.header_index.append(header.hash)
        elif self.more_work(header.hash, self.header_index):
            add, remove = self.get_fork_details(header.hash, self.header_index)
            self.header_index = self.header_index[: -len(remove)]
            self.header_index.extend(add)

    # TODO: improve speed. Current solution with set is not so bad but still suboptimal
    def update_block_candidates(self, header):
        if self.block_candidates:
            if header.previousblockhash == self.block_candidates[-1]:
                self.block_candidates.append(header.hash)
                return
            if header.previousblockhash in self.block_candidates:
                self.block_candidates.append(header.hash)
                return
        if self.more_work(header.hash):
            self.block_candidates.append(header.hash)

    def add_headers(self, headers):
        added = False  # flag that signals if there is a new header in this message
        for header in headers:
            if header.hash in self.header_dict:
                continue
            if header.previousblockhash not in self.header_dict:
                continue
            added = True
            index = self.get_block_info(header.previousblockhash).index + 1
            block_info = BlockInfo(header, index, BlockStatus.valid_header)
            self.insert_block_info(block_info)
            self.update_header_index(header)
            self.update_block_candidates(header)
        return added

    # return a list of blocks that have to be downloaded
    def get_download_candidates(self):
        candidates = []
        i = -1
        while len(candidates) < 1024:
            i += 1
            if i >= len(self.block_candidates):
                break
            candidate = self.block_candidates[i]
            if candidate not in candidates:
                new_candidates = [candidate]
                while True:
                    block_info = self.get_block_info(candidate)
                    candidate = block_info.header.previousblockhash
                    if candidate in candidates or candidate in self.active_chain:
                        break
                    if not block_info.downloaded:
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
