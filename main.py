from node import Node
import socket
import random

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
while len(node.connections) < 10:
    node.connect(addresses[i])
    i += 1

node.connect(("0.0.0.0", 8333))
