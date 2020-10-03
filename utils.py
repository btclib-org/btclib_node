from ipaddress import IPv6Address, AddressValueError


def to_ipv6(ip):
    try:
        return IPv6Address(ip)
    except AddressValueError:
        try:
            return IPv6Address("::ffff:" + ip)
        except Exception as e:
            raise e
    except Exception as e:
        raise e
