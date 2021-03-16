import enum
from dataclasses import dataclass

import plyvel
from btclib import varint
from btclib.blocks import BlockHeader
from btclib.utils import bytesio_from_binarydata


# TODO: should be implemented in btclib
def calculate_work(header):
    target = int.from_bytes(header.bits[-3:], "big")
    exp = pow(256, (header.bits[0] - 3))
    return int(256 ** 32 / target / exp)


class BlockStatus(enum.IntEnum):
    valid_header = 1
    invalid = 2
    valid = 3
    in_active_chain = 4


@dataclass
class BlockInfo:
    header: BlockHeader
    index: int
    status: BlockStatus = BlockStatus(1)
    downloaded: bool = False
    chainwork: int = 0

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
    def __init__(self, data_dir, chain, logger):

        self.logger = logger

        data_dir = data_dir / "index"
        data_dir.mkdir(exist_ok=True, parents=True)
        self.db = plyvel.DB(str(data_dir), create_if_missing=True)

        genesis = chain.genesis
        genesis_info = BlockInfo(
            genesis, 0, BlockStatus.in_active_chain, True, calculate_work(genesis)
        )

        self.header_dict = {genesis.hash: genesis_info}

        # the actual block chain; it contains only valid blocks
        self.active_chain = [genesis.hash]

        # blocks that are waiting to be connected to the active chain
        self.block_candidates = []

        # list all header hashes, even if not already checked, needed for the block locators
        self.header_index = [genesis.hash]

        self.init_from_db()

    def init_from_db(self):
        self.logger.info("Start Index initialization")
        for key, value in self.db:
            prefix, key = key[:1], key[1:]
            if prefix == b"b":
                self.header_dict[key.hex()] = BlockInfo.deserialize(value)
        self.calculate_chainwork()
        self.generate_active_chain()
        self.generate_block_candidates()
        self.generate_header_index()
        self.logger.info("Finished Index initialization")

    def close(self):
        self.logger.info("Closing Index db")
        self.db.close()

    def calculate_chainwork(self):
        sorted_dict = sorted(self.header_dict, key=lambda x: self.header_dict[x].index)
        for block_hash in sorted_dict:
            block_info = self.get_block_info(block_hash)
            if block_hash == self.active_chain[0]:  # genesis
                pass
            else:
                previous_block_hash = block_info.header.previousblockhash
                previous_block = self.get_block_info(previous_block_hash)
                new_work = previous_block.chainwork + calculate_work(block_info.header)
                block_info.chainwork = new_work
                self.insert_block_info(block_info)

    def generate_active_chain(self):
        chain_dict = {}
        for block_hash, block_info in self.header_dict.items():
            if block_info.status == BlockStatus.in_active_chain:
                chain_dict[block_info.index] = block_hash
        for index in sorted(chain_dict.keys()):
            self.active_chain.append(chain_dict[index])
        del self.active_chain[0]  # TODO: ugly, done to prevent doubles in active chain

    def generate_block_candidates(self):
        active_chain_set = set(self.active_chain)
        current_work = self.get_block_info(self.active_chain[-1]).chainwork
        sorted_dict = sorted(self.header_dict, key=lambda x: self.header_dict[x].index)
        for block_hash in sorted_dict:
            if block_hash in active_chain_set:
                continue
            block_info = self.get_block_info(block_hash)
            if block_info.status != BlockStatus.valid_header:
                continue
            header = block_info.header
            if block_info.chainwork > current_work:
                self.block_candidates.append([header.hash, block_info.chainwork])

    # TODO: improve speed
    def generate_header_index(self):
        self.header_index = self.active_chain[:]
        header_index_set = set(self.header_index)
        sorted_dict = sorted(self.header_dict, key=lambda x: self.header_dict[x].index)
        for block_hash in sorted_dict:
            if block_hash in header_index_set:
                continue
            block_info = self.get_block_info(block_hash)
            header = block_info.header
            best_header = self.header_index[-1]
            if header.previousblockhash == self.header_index[-1]:
                self.header_index.append(block_hash)
                header_index_set.add(block_hash)
            elif block_info.chainwork > self.get_block_info(best_header).chainwork:
                add, remove = self.get_fork_details(header.hash, self.header_index)
                self.header_index = self.header_index[: -len(remove)]
                self.header_index.extend(add)
                header_index_set = set(self.header_index)

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
            if header_hash == chain[block_info.index - 1]:
                anchestor_index = block_info.index - 1
                break
            else:
                fork.append(header_hash)
        main = chain[anchestor_index + 1 :]
        return fork[::-1], main

    # unsafe: doesn't perform any check
    def add_to_active_chain(self, block_hash):
        self.active_chain.append(block_hash)

    def remove_from_active_chain(self, block_hash):
        if block_hash != self.active_chain[-1]:
            raise Exception
        self.active_chain.pop()

    def get_first_candidate(self):
        chainwork = self.get_block_info(self.active_chain[-1]).chainwork
        i = 0
        if self.block_candidates:
            for hash, work in self.block_candidates:
                block_info = self.get_block_info(hash)
                if block_info.chainwork > chainwork:
                    self.block_candidates = self.block_candidates[i:]
                    return block_info
                i += 1
        return None

    def add_headers(self, headers):
        added = False  # flag that signals if there is a new header in this message
        current_work = self.get_block_info(self.active_chain[-1]).chainwork
        for header in headers:
            if header.hash in self.header_dict:
                continue
            if header.previousblockhash not in self.header_dict:
                continue
            added = True
            previous_block_info = self.get_block_info(header.previousblockhash)
            new_work = previous_block_info.chainwork + calculate_work(header)
            block_info = BlockInfo(
                header,
                previous_block_info.index + 1,
                BlockStatus.valid_header,
                False,
                new_work,
            )
            self.insert_block_info(block_info)

            if new_work > current_work:
                self.block_candidates.append([header.hash, new_work])

            best_header = self.header_index[-1]
            if header.previousblockhash == best_header:
                self.header_index.append(header.hash)
            elif new_work > self.get_block_info(best_header).chainwork:
                add, remove = self.get_fork_details(header.hash, self.header_index)
                self.header_index = self.header_index[: -len(remove)]
                self.header_index.extend(add)

        return added

    # return a list of blocks that have to be downloaded
    def get_download_candidates(self):
        chainwork = self.get_block_info(self.active_chain[-1]).chainwork
        candidates = []
        i = -1
        while len(candidates) < 1024:
            i += 1
            if i >= len(self.block_candidates):
                break
            candidate = self.block_candidates[i][0]
            if self.get_block_info(candidate).chainwork < chainwork:
                continue
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
                end = output.index(stop)
                output = output[: end + 1]
            output = output[:2000]
            break
        return [self.get_block_info(x).header for x in output]
