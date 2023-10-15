from pathlib import Path

from btclib.script.engine import verify_transaction
from btclib.tx.tx import Tx
from btclib.tx.tx_out import TxOut
from btclib.utils import bytesio_from_binarydata


def get_error_data(id, i):
    err_dir = Path("errors", id, str(i))
    with open(err_dir / "flags") as f:
        flags = tuple(
            f.read().replace("'", "").replace("(", "").replace(")", "").split(", ")
        )
    with open(err_dir / "tx", "rb") as f:
        tx = Tx.parse(f.read())
    with open(err_dir / "prevouts", "rb") as f:
        s = bytesio_from_binarydata(f.read())
        prevouts = []
        while True:
            try:
                prevouts.append(TxOut.parse(s))
            except Exception:
                break
    return prevouts, tx, flags


for x in Path("errors").iterdir():
    txid = x.name
    for y in x.iterdir():
        vin = y.name
        print(txid, vin)
        try:
            verify_transaction(*get_error_data(txid, vin))
        except Exception:
            print("error")
        # print(txid, vin)
        # verify_transaction(*get_error_data(txid, vin))
