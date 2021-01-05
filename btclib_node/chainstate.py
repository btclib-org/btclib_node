import os

import plyvel
from btclib.tx_in import OutPoint
from btclib.tx_out import TxOut


class Chainstate:
    def __init__(self, data_dir):
        data_dir = os.path.join(data_dir, "chainstate")
        os.makedirs(data_dir, exist_ok=True)
        self.db = plyvel.DB(data_dir, create_if_missing=True)
        self.utxo_dict = {}
        # for key, value in self.db:
        #     key = key.hex()
        #     value = TxOut.deserialize(value)
        #     self.utxo_dict[key] = value

    def get_prev_outputs(self, tx):
        outputs = []
        for tx_in in tx.vin:
            outputs.append(self.utxo_dict[tx_in.prevout])

    def add_transaction(self, tx):
        for tx_in in tx.vin:
            self.utxo_dict.pop(tx_in.prevout)
            # self.db.delete(bytes.fromhex(tx_in.prevout))
        for i, tx_out in enumerate(tx.vout):
            out_point = OutPoint(tx.txid, i)
            self.utxo_dict[out_point.serialize().hex()] = tx_out
            # self.db.put(out_point.serialize(), tx_out.serialize())
