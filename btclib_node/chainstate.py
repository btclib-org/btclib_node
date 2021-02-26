import plyvel
from btclib.tx_in import OutPoint
from btclib.tx_out import TxOut

from btclib_node.block_db import RevBlock


class Chainstate:
    def __init__(self, data_dir):
        data_dir = data_dir / "chainstate"
        data_dir.mkdir(exist_ok=True, parents=True)
        self.db = plyvel.DB(str(data_dir), create_if_missing=True)
        self.utxo_dict = {}
        self.init_from_db()

    def init_from_db(self):
        for key, value in self.db:
            key = key.hex()
            value = TxOut.deserialize(value)
            self.utxo_dict[key] = value

    def get_output(self, out_point):
        prev_out_hash = out_point.serialize().hex()
        if prev_out_hash in self.utxo_dict:
            return self.utxo_dict[prev_out_hash]
        return None

    def __add_output(self, out_point, tx_out):
        self.utxo_dict[out_point.serialize().hex()] = tx_out
        self.db.put(out_point.serialize(), tx_out.serialize())

    def __remove_output(self, out_point):
        self.utxo_dict.pop(out_point.serialize().hex())
        self.db.delete(out_point.serialize())

    def add_block(self, block):
        removed = []
        added = []
        for i, tx_out in enumerate(block.transactions[0].vout):
            out_point = OutPoint(block.transactions[0].txid, i)
            self.__add_output(out_point, tx_out)
            added.append(out_point)
        for tx in block.transactions[1:]:
            for tx_in in tx.vin:
                removed.append((tx_in.prevout, self.get_output(tx_in.prevout)))
                self.__remove_output(tx_in.prevout)
            for i, tx_out in enumerate(tx.vout):
                out_point = OutPoint(tx.txid, i)
                self.__add_output(out_point, tx_out)
                added.append(out_point)
        rev_block = RevBlock(hash=block.header.hash, to_add=removed, to_remove=added)
        return rev_block

    def apply_rev_block(self, rev_block):
        for out_point in rev_block.to_remove:
            self.__remove_output(out_point)
        for out_point, tx_out in rev_block.to_add:
            self.__add_output(out_point, tx_out)
