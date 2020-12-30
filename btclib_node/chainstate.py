import os

import plyvel
from btclib.tx_out import TxOut
from btclib.tx_in import OutPoint


class Chainstate:
    def __init__(self, data_dir):
        data_dir = os.path.join(data_dir, "chainstate")
        os.makedirs(data_dir, exist_ok=True)
        self.db = plyvel.DB(data_dir, create_if_missing=True)
        self.transactions = {}

    def add_transaction(tx):
        pass
