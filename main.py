import logging

from btclib_node.node import Node

logging.getLogger("asyncio").setLevel(logging.DEBUG)

node = Node(30000)
node.start()
