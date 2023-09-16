from btclib_node.mempool import Mempool
from tests.helpers import generate_random_transaction


def test_init():
    Mempool()


def test_workflow():
    mempool = Mempool()

    tx = generate_random_transaction()
    mempool.add_tx(tx)

    assert mempool.size == 1
    assert mempool.bytesize == tx.vsize
    assert mempool.get_tx(tx.id) == tx

    mempool.remove_tx(tx.id)
    assert mempool.size == 0
    assert mempool.bytesize == 0
 
    txs = []
    for x in range(100):
        tx = generate_random_transaction()
        mempool.add_tx(tx)
        txs.append(tx)
        
    prev_size = mempool.size
    prev_bytesize = mempool.bytesize
    # Test is_full() method
    mempool.bytesize_limit = mempool.bytesize
    mempool.add_tx(generate_random_transaction())
    assert prev_size == mempool.size
    assert prev_bytesize == mempool.bytesize

    tx = generate_random_transaction()
    mempool.bytesize_limit = 1000**2
    assert mempool.get_missing([tx.id for tx in txs] + [tx.id]) == [tx.id]

    assert mempool.get_tx(b"\x00"*32) == None
