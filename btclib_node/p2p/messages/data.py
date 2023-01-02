from dataclasses import dataclass
from typing import List, Tuple

from btclib import var_int
from btclib.tx.blocks import Block as BlockData
from btclib.tx.blocks import BlockHeader
from btclib.tx.tx import Tx as TxData
from btclib.utils import bytesio_from_binarydata

from btclib_node.p2p.messages import add_headers


@dataclass
class Tx:
    tx: TxData
    include_witness: bool = True

    @classmethod
    def deserialize(cls, data):
        tx = TxData.parse(data)
        return cls(tx)

    def serialize(self):
        data = self.tx.serialize(self.include_witness)
        return add_headers("tx", data)


@dataclass
class Block:
    block: BlockData
    include_witness: bool = True

    @classmethod
    def deserialize(cls, data, check_validity=True):
        block = BlockData.parse(data, check_validity)
        return cls(block)

    def serialize(self):
        data = self.block.serialize(self.include_witness)
        return add_headers("block", data)


@dataclass
class Headers:
    headers: List[BlockHeader]

    @classmethod
    def deserialize(cls, data):
        stream = bytesio_from_binarydata(data)
        headers_num = var_int.parse(stream)
        headers = []
        for _ in range(headers_num):
            header = BlockHeader.parse(stream)
            stream.read(1)
            headers.append(header)
        return cls(headers)

    def serialize(self):
        payload = var_int.serialize(len(self.headers))
        for header in self.headers:
            payload += header.serialize()
            payload += b"\x00"
        return add_headers("headers", payload)


@dataclass
class Blocktxn:
    blockhash: bytes
    transactions: List[TxData]
    include_witness: bool = True

    @classmethod
    def deserialize(cls, data):
        stream = bytesio_from_binarydata(data)
        blockhash = stream.read(32)[::-1]
        num_transactions = var_int.parse(stream)
        transactions = [TxData.parse(stream) for _ in range(num_transactions)]
        return cls(blockhash=blockhash, transactions=transactions)

    def serialize(self):
        payload = self.blockhash[::-1]
        payload += var_int.serialize(len(self.transactions))
        for tx in self.transactions:
            payload += tx.serialize(self.include_witness)
        return add_headers("blocktxn", payload)


@dataclass
class Inv:
    inventory: List[Tuple[int, bytes]]

    @classmethod
    def deserialize(cls, data):
        stream = bytesio_from_binarydata(data)
        inventory_length = var_int.parse(stream)
        inventory = []
        for _ in range(inventory_length):
            item_type = int.from_bytes(stream.read(4), "little")
            item_hash = stream.read(32)[::-1]
            inventory.append((item_type, item_hash))
        return cls(inventory)

    def serialize(self):
        payload = var_int.serialize(len(self.inventory))
        for item in self.inventory:
            payload += item[0].to_bytes(4, "little")
            payload += item[1][::-1]
        return add_headers("inv", payload)
