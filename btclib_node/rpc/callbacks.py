def getbestblockhash(node, _, conn):
    conn.send(node.index.index[-1])


callbacks = {"getbestblockhash": getbestblockhash}
