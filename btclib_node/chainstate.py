from dataclasses import dataclass
from typing import Dict

from btclib.tx import Tx


@dataclass
class Chainstate:
    transactions: Dict[str, Tx]
