from dataclasses import dataclass
from typing import List, Tuple

import plyvel
from btclib import varint
from btclib.blocks import Block
from btclib.tx_in import OutPoint
from btclib.tx_out import TxOut
from btclib.utils import bytesio_from_binarydata


@dataclass
class RevBlock:
    hash: str
    to_add: List[Tuple[OutPoint, TxOut]]
    to_remove: List[OutPoint]

    @classmethod
    def deserialize(cls, data):
        stream = bytesio_from_binarydata(data)
        hash = stream.read(32).hex()
        to_add = []
        for x in range(varint.decode(stream)):
            out_point = OutPoint.deserialize(stream)
            tx_out = TxOut.deserialize(stream)
            to_add.append([out_point, tx_out])
        to_remove = []
        for x in range(varint.decode(stream)):
            out_point = OutPoint.deserialize(stream)
            to_remove.append(out_point)
        return cls(hash, to_add, to_remove)

    def serialize(self):
        out = bytes.fromhex(self.hash)
        out += varint.encode(len(self.to_add))
        for out_point, tx_out in self.to_add:
            out += out_point.serialize()
            out += tx_out.serialize()
        out += varint.encode(len(self.to_remove))
        for out_point in self.to_remove:
            out += out_point.serialize()
        return out


@dataclass
class BlockLocation:
    filename: str
    index: int
    size: int

    @classmethod
    def deserialize(cls, data):
        stream = bytesio_from_binarydata(data)
        filename = stream.read(10).decode()
        index = varint.deserialize(stream)
        size = varint.deserialize(stream)
        return cls(filename, index, size)

    def serialize(self):
        out = self.filename.encode()
        out += varint.encode(self.index)
        out += varint.encode(self.size)
        return out


@dataclass
class FileMetadata:
    filename: str
    size: int

    @classmethod
    def deserialize(cls, data):
        stream = bytesio_from_binarydata(data)
        filename = stream.read(10).decode()
        size = varint.deserialize(stream)
        return cls(filename, size)

    def serialize(self):
        out = self.filename.encode()
        out += varint.encode(self.size)
        return out


# TODO: use more than one file
class BlockDB:
    def __init__(self, data_dir):
        self.data_dir = data_dir / "blocks"
        self.data_dir.mkdir(exist_ok=True, parents=True)
        self.db = plyvel.DB(str(self.data_dir), create_if_missing=True)
        self.files = {}
        self.blocks = {}
        self.rev_patches = {}
        self.init_from_db()
        if not self.files:
            self.files["data.blk"] = FileMetadata("data.blk", 0)
            self.files["data.rev"] = FileMetadata("data.rev", 0)
        self.current_block_file = None
        self.current_rev_file = None

    def init_from_db(self):
        for key, value in self.db:
            if key[:1] == b"f":
                self.files[key[1:].hex()] = FileMetadata.deserialize(value)
            elif key[:1] == b"b":
                self.blocks[key[1:].hex()] = BlockLocation.deserialize(value)
            elif key[:1] == b"r":
                self.rev_patches[key[1:].hex()] = BlockLocation.deserialize(value)

    def close(self):
        self.db.close()

    def __get_file(self, filename):
        if filename[-3:] == "blk":
            if not self.current_block_file:
                self.current_block_file = open(str(self.data_dir / filename), "a+b")
            if self.current_block_file.name[-len(filename) :] != filename:
                self.current_block_file.close()
                self.current_block_file = open(str(self.data_dir / filename), "a+b")
            return self.current_block_file
        elif filename[-3:] == "rev":
            if not self.current_rev_file:
                self.current_rev_file = open(str(self.data_dir / filename), "a+b")
            if self.current_rev_file.name[-len(filename) :] != filename:
                self.current_rev_file.close()
                self.current_rev_file = open(str(self.data_dir / filename), "a+b")
            return self.current_rev_file

    def __add_to_file(self, filename, data):
        file = self.__get_file(filename)
        file.write(data)
        file.flush()
        file_metadata = self.files[filename]
        data_index = file_metadata.size
        data_size = len(data)
        file_metadata.size += data_size
        self.db.put(b"f" + file_metadata.filename.encode(), file_metadata.serialize())
        return data_index, data_size

    def __get_from_file(self, filename, index, size):
        file = self.__get_file(filename)
        file.seek(index)
        data = file.read(size)
        return data

    def add_block(self, block):
        data = block.serialize()
        filename = "data.blk"
        index, block_size = self.__add_to_file(filename, data)
        block_location = BlockLocation(filename, index, block_size)
        self.blocks[block.header.hash] = block_location
        self.db.put(b"f" + bytes.fromhex(block.header.hash), block_location.serialize())

    def add_rev_block(self, rev_block):
        data = rev_block.serialize()
        filename = "data.rev"
        index, block_size = self.__add_to_file(filename, data)
        block_location = BlockLocation(filename, index, block_size)
        self.rev_patches[rev_block.hash] = block_location
        self.db.put(b"f" + bytes.fromhex(rev_block.hash), block_location.serialize())

    def get_block(self, hash):
        if hash not in self.blocks:
            return None
        filename = "data.blk"
        block_location = self.blocks[hash]
        block_data = self.__get_from_file(
            filename, block_location.index, block_location.size
        )
        return Block.deserialize(block_data)

    def get_rev_block(self, hash):
        if hash not in self.rev_patches:
            return None
        filename = "data.rev"
        rev_patch_location = self.rev_patches[hash]
        rev_patch_data = self.__get_from_file(
            filename, rev_patch_location.index, rev_patch_location.size
        )
        return RevBlock.deserialize(rev_patch_data)
