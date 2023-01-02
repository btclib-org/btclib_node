from dataclasses import dataclass, field
from typing import Dict

from btclib.tx.tx import Tx


@dataclass
class Mempool:
    transactions: Dict[bytes, Tx] = field(default_factory=lambda: {})
    size: int = 0

    def is_full(self):
        return self.size > 1000 ** 3  # 1GB

    def get_missing(self, transactions):
        missing = []
        if not self.is_full():
            missing.extend(tx for tx in transactions if tx not in self.transactions)
        return missing

    def get_tx(self, txid):
        return self.transactions[txid] if txid in self.transactions else None

    def add_tx(self, tx):
        if not self.is_full():
            self.transactions[tx.id] = tx
            self.size += len(tx.serialize(include_witness=True))

    def remove_tx(self, tx_id):
        if tx_id in self.transactions:
            tx = self.transactions.pop(tx_id)
            self.size -= len(tx.serialize(include_witness=True))
