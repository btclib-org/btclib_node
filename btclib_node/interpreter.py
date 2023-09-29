import traceback
from itertools import chain
from pathlib import Path
from typing import Tuple
from copy import deepcopy

from btclib.script.engine import verify_input, verify_transaction


def get_flags(config, index) -> Tuple[str]:
    return tuple(f for (i, f) in config.chain.flags if index >= i)


def f(prevouts, tx, i, flags):
    try:
        # no need to deepcopy the values as 
        # they are not reused
        # TODO: are we really sure this is safe?
        # To check and fix upstream
        verify_input(prevouts, tx, i, flags)
    except Exception as e:
        err_dir = Path("errors", tx.id.hex(), str(i))
        err_dir.mkdir(parents=True, exist_ok=True)
        with open(err_dir / "flags", "w") as f:
            f.write(str(flags))
        with open(err_dir / "tx", "wb") as f:
            f.write(tx.serialize(True))
        with open(err_dir / "exception", "w") as f:
            f.write(traceback.format_exc())
        with open(err_dir / "prevouts", "wb") as f:
            for pv in prevouts:
                f.write(pv.serialize())


def check_transactions(transaction_data, index, node):

    if not transaction_data:
        return
    if any(len(x[0]) != len(x[1].vin) for x in transaction_data):
        raise ValueError()

    # for prev_outputs, tx in transaction_data:
    #     verify_transaction(prev_outputs, tx, FLAGS)

    FLAGS = get_flags(node.config, index)

    node.worker_pool.starmap(
        f,
        chain.from_iterable(
            ((x[0], x[1], i, FLAGS) for i in range(len(x[0]))) for x in transaction_data
        ),
    )


def check_transaction(prevouts, tx, index, node):
    # TODO: we need to deepcopy the transaction because
    # verify_transaction modifies it. To fix upstream
    tx = deepcopy(tx)
    flags = get_flags(node.config, index)
    verify_transaction(prevouts, tx, flags)
