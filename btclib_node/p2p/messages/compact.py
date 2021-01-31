from dataclasses import dataclass
from typing import List, Tuple

from btclib import varint
from btclib.blocks import BlockHeader
from btclib.tx import Tx
from btclib.utils import bytesio_from_binarydata

from btclib_node.p2p.messages import add_headers


@dataclass
class Sendcmpct:
    flag: bool
    version: int

    @classmethod
    def deserialize(cls, data):
        stream = bytesio_from_binarydata(data)
        flag = bool(stream.read(1)[0])
        version = int.from_bytes(stream.read(8), "little")
        return cls(flag, version)

    def serialize(self):
        payload = int(self.flag).to_bytes(1, "little")
        payload += self.version.to_bytes(8, "little")
        return add_headers("sendcmpt", payload)


@dataclass
class Cmpctblock:
    header: BlockHeader
    nonce: int
    short_ids: List[str]
    prefilled_tx_list: List[Tuple[int, Tx]]

    @classmethod
    def deserialize(cls, data):
        stream = bytesio_from_binarydata(data)
        header = BlockHeader.deserialize(stream)
        nonce = int.from_bytes(stream.read(8), "little")
        short_ids = []
        short_ids_length = varint.decode(stream)
        for x in range(short_ids_length):
            short_ids.append(stream.read(6)[::-1].hex())
        prefilled_tx_list = []
        prefilled_tx_num = varint.decode(stream)
        for x in range(prefilled_tx_num):
            tx_index = varint.decode(stream)
            tx = Tx.deserialize(stream)
            prefilled_tx_list.append((tx_index, tx))
        return cls(
            header=header,
            nonce=nonce,
            short_ids=short_ids,
            prefilled_tx_list=prefilled_tx_list,
        )

    def serialize(self):
        payload = self.header.serialize()
        payload += self.nonce.to_bytes(8, "little")
        payload += varint.encode(len(self.short_ids))
        for short_id in self.short_ids:
            payload += bytes.fromhex(short_id)[::-1]
        payload += varint.encode(len(self.prefilled_tx_list))
        for tx_index, tx in self.prefilled_tx_list:
            payload += varint.encode(tx_index)
            payload += tx.serialize()
        return add_headers("cmptblock", payload)
