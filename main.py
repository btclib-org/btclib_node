import random
import socket
import sys
import time

from btclib_node.net.messages.getdata import Getheaders, Sendheaders
from btclib_node.node import Node

node = Node(30000)
node.start()

dns_servers = [
    "seed.bitcoin.sipa.be",
    "dnsseed.bluematt.me",
    "dnsseed.bitcoin.dashjr.org",
    "seed.bitcoinstats.com",
    "seed.bitcoin.jonasschnelli.ch",
    "seed.btc.petertodd.org",
    "seed.bitcoin.sprovoost.nl",
    "dnsseed.emzy.de",
    "seed.bitcoin.wiz.biz",
]

addresses = []
for dns_server in dns_servers:
    try:
        ips = socket.getaddrinfo(dns_server, 8333)
    except socket.gaierror:
        continue
    for ip in ips:
        addresses.append(ip[4])

random.shuffle(addresses)

i = 0
while len(node.connection_manager.connections) < 10:
    node.connect(addresses[i][0], addresses[i][1])
    i += 1

node.connect("0.0.0.0", 8333)
id = max(node.connection_manager.connections.keys())
node.connection_manager.connections[id].send(Sendheaders())

first_block_hash = "000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8ce26f"
node.connection_manager.connections[id].send(
    Getheaders(7015, [first_block_hash], "00" * 32)
)

while True:
    try:
        time.sleep(0.1)
    except KeyboardInterrupt:
        node.stop()
        time.sleep(0.25)
        sys.exit()
