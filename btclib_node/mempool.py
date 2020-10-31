from dataclasses import dataclass
from typing import Dict

from btclib.tx import Tx

from btclib_node.net.messages.getdata import Getdata


@dataclass
class Mempool:
    transactions: Dict[str, Tx]

    def get_missing(self, transactions):
        missing = []
        for tx in transactions:
            if tx not in self.transactions:
                missing.append([1, tx])
        return Getdata(missing)

    def add_tx(self, tx):
        self.transactions[tx.txid] = tx
