from btclib_node.p2p.address import NetworkAddress, to_ipv6


def test_to_ipv6():
    ipv4 = "127.0.0.1"
    ipv6 = to_ipv6(ipv4)
    assert ipv6.ipv4_mapped.compressed == ipv4


def test_serialization():
    for x in range(1, 129):
        ipv6 = to_ipv6(2 ** x - 1)
        for y in range(10):
            services = 2 ** y
            for z in range(1, 17):
                port = 2 ** z - 1
                network_address = NetworkAddress(services, ipv6, port)
                assert network_address == NetworkAddress.deserialize(
                    network_address.serialize()
                )
