from dataclasses import dataclass, field
from typing import Dict

from btclib.tx.tx import Tx


@dataclass
class Mempool:
    transactions: Dict[bytes, Tx] = field(default_factory=lambda: {})
    size: int = 0
    bytesize: int = 0
    bytesize_limit: int = 500 * 1000**2  # 500vMB

    def is_full(self):
        return self.bytesize >= self.bytesize_limit

    def get_missing(self, transactions):
        missing = []
        if not self.is_full():
            for tx_id in transactions:
                if tx_id not in self.transactions:
                    missing.append(tx_id)
        return missing

    def get_tx(self, txid):
        if txid in self.transactions:
            return self.transactions[txid]
        return None

    def add_tx(self, tx):
        if not self.is_full():
            self.transactions[tx.id] = tx
            self.size += 1
            self.bytesize += tx.vsize

    def remove_tx(self, tx_id):
        if tx_id in self.transactions:
            tx = self.transactions.pop(tx_id)
            self.size -= 1
            self.bytesize -= tx.vsize
