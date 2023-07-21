import plyvel
from btclib.tx.tx_in import OutPoint
from btclib.tx.tx_out import TxOut

from btclib_node.block_db import RevBlock


class Chainstate:
    def __init__(self, data_dir, logger):
        data_dir = data_dir / "chainstate"
        data_dir.mkdir(exist_ok=True, parents=True)

        self.db = plyvel.DB(str(data_dir), create_if_missing=True)
        self.removed_utxos = set()
        self.updated_utxo_set = {}

        self.logger = logger

    def close(self):
        self.logger.info("Closing Chainstate db")
        self.db.close()

    def add_block(self, block):

        removed = []
        added = []
        complete_transactions = []

        for i, tx_out in enumerate(block.transactions[0].vout):
            out_point = OutPoint(block.transactions[0].id, i, check_validity=False)
            self.updated_utxo_set[out_point.serialize(check_validity=False)] = tx_out
            added.append(out_point)

        for tx in block.transactions[1:]:

            tx_id = tx.id

            prev_outputs = []

            for tx_in in tx.vin:

                prevout_bytes = tx_in.prev_out.serialize(check_validity=False)

                if prevout_bytes in self.removed_utxos:
                    raise Exception
                if prevout_bytes in self.updated_utxo_set:
                    prevout = self.updated_utxo_set[prevout_bytes]
                    prev_outputs.append(prevout)
                    self.updated_utxo_set.pop(prevout_bytes)
                else:
                    prevout = self.db.get(prevout_bytes)
                    if prevout:
                        prevout = TxOut.parse(prevout, check_validity=False)
                        prev_outputs.append(prevout)
                        self.removed_utxos.add(prevout_bytes)
                    else:
                        raise Exception

                removed.append((tx_in.prev_out, prevout))

            for i, tx_out in enumerate(tx.vout):
                out_point = OutPoint(tx_id, i, check_validity=False)
                self.updated_utxo_set[
                    out_point.serialize(check_validity=False)
                ] = tx_out
                added.append(out_point)

            complete_transactions.append([prev_outputs, tx])

        rev_block = RevBlock(hash=block.header.hash, to_add=removed, to_remove=added)

        return complete_transactions, rev_block

    def apply_rev_block(self, rev_block):
        for out_point in rev_block.to_remove:

            out_point_bytes = out_point.serialize(check_validity=False)

            if out_point_bytes in self.removed_utxos:
                raise Exception
            if out_point_bytes in self.updated_utxo_set:
                self.updated_utxo_set.pop(out_point_bytes)
            else:
                if self.db.get(out_point_bytes):
                    self.removed_utxos.add(out_point_bytes)
                else:
                    raise Exception

        for out_point, tx_out in rev_block.to_add:
            self.updated_utxo_set[out_point.serialize(check_validity=False)] = tx_out

    def finalize(self):
        with self.db.write_batch(transaction=True) as wb:
            for x in self.removed_utxos:
                wb.delete(x)
            for out_point_bytes, tx_out in self.updated_utxo_set.items():
                wb.put(out_point_bytes, tx_out.serialize())
        self.removed_utxos = set()
        self.updated_utxo_set = {}

    def rollback(self):
        self.removed_utxos = set()
        self.updated_utxo_set = {}
