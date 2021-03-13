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
        self.removed_utxos = []
        self.updated_utxo_set = {}

        self.init_from_db()

    def init_from_db(self):
        for key, value in self.db:
            key = key.hex()
            value = TxOut.deserialize(value)
            self.utxo_dict[key] = value

    def close(self):
        self.db.close()

    def get_output(self, out_point):
        prev_out_hash = out_point.serialize().hex()
        if prev_out_hash in self.utxo_dict:
            return self.utxo_dict[prev_out_hash]
        return None

    def add_block(self, block):

        removed = []
        added = []
        complete_transactions = []

        for i, tx_out in enumerate(block.transactions[0].vout):
            out_point = OutPoint(block.transactions[0].txid, i)
            self.updated_utxo_set[out_point.serialize().hex()] = tx_out
            added.append(out_point)

        for tx in block.transactions[1:]:

            prev_outputs = []

            for tx_in in tx.vin:

                prevout_hex = tx_in.prevout.serialize().hex()

                if prevout_hex in self.removed_utxos:
                    raise Exception
                if prevout_hex in self.updated_utxo_set:
                    prevout = self.updated_utxo_set[prevout_hex]
                    prev_outputs.append(prevout)
                    self.updated_utxo_set.pop(prevout_hex)
                elif prevout_hex in self.utxo_dict:
                    prevout = self.utxo_dict[prevout_hex]
                    prev_outputs.append(prevout)
                    self.removed_utxos.append(prevout_hex)
                else:
                    raise Exception

                removed.append((tx_in.prevout, prevout))

            for i, tx_out in enumerate(tx.vout):
                out_point = OutPoint(tx.txid, i)
                self.updated_utxo_set[out_point.serialize().hex()] = tx_out
                added.append(out_point)

            complete_transactions.append([prev_outputs, tx])

        rev_block = RevBlock(hash=block.header.hash, to_add=removed, to_remove=added)

        return complete_transactions, rev_block

    def apply_rev_block(self, rev_block):
        for out_point in rev_block.to_remove:

            out_point_hex = out_point.serialize().hex()

            if out_point_hex in self.removed_utxos:
                raise Exception
            if out_point_hex in self.updated_utxo_set:
                self.updated_utxo_set.pop(out_point_hex)
            elif out_point_hex in self.utxo_dict:
                self.removed_utxos.append(out_point_hex)
            else:
                raise Exception

        for out_point, tx_out in rev_block.to_add:
            self.updated_utxo_set[out_point.serialize().hex()] = tx_out

    def finalize(self):
        for x in self.removed_utxos:
            self.utxo_dict.pop(x)
            self.db.delete(bytes.fromhex(x))
        for out_point_hex, tx_out in self.updated_utxo_set.items():
            self.utxo_dict[out_point_hex] = tx_out
            self.db.put(bytes.fromhex(out_point_hex), tx_out.serialize())
        self.removed_utxos = []
        self.updated_utxo_set = {}

    def rollback(self):
        self.removed_utxos = []
        self.updated_utxo_set = {}
