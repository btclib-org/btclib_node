from dataclasses import dataclass, field
from typing import Dict

from btclib.tx.tx import Tx


class Mempool:

    def __init__(self, logger):

        self.logger = logger

        self.transactions: Dict[bytes, Tx] = {}
        self.txid_index: Dict[bytes, bytes] = {}
        self.size: int = 0
        self.bytesize: int = 0
        self.bytesize_limit: int = 500 * 1000**2  # 500vMB

    def is_full(self):
        return self.bytesize >= self.bytesize_limit

    def get_missing(self, transactions, wtxid=False):
        if self.is_full():
            return []
        missing = []
        index = self.transactions if wtxid else self.txid_index
        for tx_id in transactions:
            if tx_id not in index:
                missing.append(tx_id)
        return missing

    def get_tx(self, txid, wtxid=False):
        if not wtxid:
            txid = self.txid_index.get(txid)
        return self.transactions.get(txid)

    def add_tx(self, tx):
        if not self.is_full() and not tx.hash in self.transactions:
            self.transactions[tx.hash] = tx
            self.txid_index[tx.id] = tx.hash
            self.size += 1
            self.bytesize += tx.vsize

    def remove_tx(self, tx_id):
        if tx_id in self.transactions:
            tx = self.transactions.pop(tx_id)
            self.txid_index.pop(tx.id)
            self.size -= 1
            self.bytesize -= tx.vsize

    def contains_tx(self, tx):
        return tx.hash in self.transactions
