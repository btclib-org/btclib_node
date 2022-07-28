from btclib.script.engine import verify_transaction, verify_input
import traceback
from multiprocessing.pool import Pool
from os import cpu_count
from math import ceil
from itertools import chain
from pathlib import Path

import sys

_FLAGS_ = [
    "P2SH",
    "SIGPUSHONLY",
    # "LOW_S",
    "STRICTENC",
    "DERSIG",
    "CONST_SCRIPTCODE",
    "NULLDUMMY",
    "CLEANSTACK",
    "MINIMALDATA",
    # only standard, not consensus
    # "NULLFAIL",
    # "MINMALIF",
    # "DISCOURAGE_UPGRADABLE_NOPS",
    # "DISCOURAGE_UPGRADABLE_WITNESS_PROGRAM",
    "CHECKLOCKTIMEVERIFY",
    "CHECKSEQUENCEVERIFY",
    "WITNESS",
    "WITNESS_PUBKEYTYPE",
    "TAPROOT",
]


def f(prevouts, tx, i, flags):
    try:
        verify_input(prevouts, tx, i, flags)
    except Exception as e:
        err_dir = Path('errors', tx.id.hex(), str(i))
        err_dir.mkdir(parents=True, exist_ok=True)
        with open(err_dir / 'flags', 'w') as f:
            f.write(str(flags))
        with open(err_dir / 'tx', 'wb') as f:
            f.write(tx.serialize(True))
        with open(err_dir / 'exception', 'w') as f:
            f.write(traceback.format_exc())
        with open(err_dir / 'prevouts', 'wb') as f:
            for pv in prevouts:
                f.write(pv.serialize())
        

def check_transactions(transaction_data, index, node):

    if not transaction_data:
        return

    FLAGS = []

    # only for testnet
    if index >= 395:
        FLAGS += ["P2SH"]
    if index >= 330776:
        FLAGS += ["DERSIG"]
    if index >= 581885:
        FLAGS += ["CHECKLOCKTIMEVERIFY"]
    if index >= 770112:
        FLAGS += ["CHECKSEQUENCEVERIFY"]
    if index >= 834624:
        FLAGS += ["WITNESS", "WITNESS_PUBKEYTYPE", "NULLDUMMY"]
    if index >= 1628640000:
        FLAGS += ["TAPROOT"]

    # for prev_outputs, tx in transaction_data:
    #     verify_transaction(prev_outputs, tx, FLAGS)

    if any(len(x[0]) != len(x[1].vin) for x in transaction_data):
        raise ValueError()

    FLAGS = tuple(FLAGS)

    node.worker_pool.starmap(
        f,
        chain.from_iterable(
            ((x[0], x[1], i, FLAGS) for i in range(len(x[0]))) for x in transaction_data
        ),
    )
