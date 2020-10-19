from ipaddress import AddressValueError, IPv6Address


def to_ipv6(ip):
    try:
        return IPv6Address(ip)
    except AddressValueError:
        return IPv6Address("::ffff:" + ip)
    except Exception as e:
        raise e
