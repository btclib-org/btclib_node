from dataclasses import dataclass, field
from typing import Dict

from btclib.tx import Tx


@dataclass
class Chainstate:
    transactions: Dict[str, Tx] = field(default_factory=lambda: {})
