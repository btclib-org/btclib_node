from pathlib import Path

from btclib_node import *
from btclib_node.chains import TestNet

data_dir = Path(".btclib/testnet")
logger = Logger(data_dir / "log")
index = BlockIndex(data_dir, TestNet(), logger)
