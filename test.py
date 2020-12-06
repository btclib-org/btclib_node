from btclib import tx, tx_in, tx_out

coinbase = "01000000010000000000000000000000000000000000000000000000000000000000000000ffffffff0704ffff001d0104ffffffff0100f2052a0100000043410496b538e853519c726a2c91e61ec11600ae1390813a627c66fb8be7947be63c52da7589379515d4e0a604f8141781e62294721166bf621e73a82cbf2342c858eeac00000000"
transaction = tx.Tx.deserialize(coinbase)
assert transaction.serialize().hex() == coinbase

coinbase_inp = "0000000000000000000000000000000000000000000000000000000000000000ffffffff0704ffff001d0104ffffffff"
transaction_in = tx_in.TxIn.deserialize(coinbase_inp)
assert transaction_in.serialize().hex() == coinbase_inp
assert transaction_in.prevout.is_coinbase

coinbase_out = "00f2052a0100000043410496b538e853519c726a2c91e61ec11600ae1390813a627c66fb8be7947be63c52da7589379515d4e0a604f8141781e62294721166bf621e73a82cbf2342c858eeac"
transaction_out = tx_out.TxOut.deserialize(coinbase_out)
assert transaction_out.serialize().hex() == coinbase_out

assert transaction.vin[0].scriptSig == transaction_in.scriptSig
assert transaction.vout[0].scriptPubKey == transaction_out.scriptPubKey

assert transaction.txid == bytes.fromhex(
    "0e3e2357e806b6cdb1f70b54c3a3a17b6714ee1f0e68bebb44a74b1efd512098"
)
assert transaction.txid == transaction.hash

assert transaction.size == 134
assert transaction.weight == 536
assert transaction.vsize == transaction.size
