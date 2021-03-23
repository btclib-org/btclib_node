from dataclasses import dataclass, field
from typing import Dict

from btclib.tx import Tx


@dataclass
class Mempool:
    transactions: Dict[str, Tx] = field(default_factory=lambda: {})
    size: int = 0

    def is_full(self):
        return self.size > 1000 ** 3  # 1GB

    def get_missing(self, transactions):
        missing = []
        if not self.is_full():
            for tx in transactions:
                if tx not in self.transactions:
                    missing.append(tx)
        return missing

    def get_tx(self, txid):
        if txid in self.transactions:
            return self.transactions[txid]
        return None

    def add_tx(self, tx):
        if not self.is_full():
            self.transactions[tx.txid] = tx
            self.size += len(tx.serialize())

    def remove_tx(self, tx_id):
        if tx_id in self.transactions:
            tx = self.transactions.pop(tx_id)
            self.size -= len(tx.serialize())
