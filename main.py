import time

from btclib_node.net.messages.address import Getaddr
from btclib_node.net.messages.getdata import Getheaders, Sendheaders
from btclib_node.node import Node

node = Node(30000)
node.start()

node.connect("0.0.0.0", 8333)
id = max(node.connection_manager.connections.keys())
node.connection_manager.connections[id].send(Sendheaders())

first_block_hash = "000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8ce26f"
node.connection_manager.connections[id].send(
    Getheaders(7015, [first_block_hash], "00" * 32)
)

time.sleep(10)
node.connection_manager.send(Getaddr(), 1)
