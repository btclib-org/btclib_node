from btclib.utils import bytesio_from_binarydata
from btclib.tx.tx import Tx
from btclib.tx.tx_out import TxOut
from pathlib import Path


def get_error_data(id, i):
    err_dir = Path('errors', id, str(i))
    with open(err_dir / 'flags', 'r') as f:
        flags = tuple(f.read().replace("'", "").replace("(", "").replace(")", "").split(','))
    with open(err_dir / 'tx', 'rb') as f:
        tx = Tx.parse(f.read())
    with open(err_dir / 'prevouts', 'rb') as f:
        s = bytesio_from_binarydata(f.read())
        prevouts = []
        while True:
            try:
                prevouts.append(TxOut.parse(s))
            except:
                break
    return prevouts, tx, flags