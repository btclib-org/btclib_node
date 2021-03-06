import struct
from hashlib import sha256


class WrongChecksumError(Exception):
    pass


# does not add p2pwork_string
def add_headers(name: str, payload: bytes):
    command = name + ((12 - len(name)) * "\00")
    payload_len = struct.pack("I", len(payload))
    checksum = sha256(sha256(payload).digest()).digest()[:4]
    return command.encode() + payload_len + checksum + payload


def verify_headers(message: bytes):
    payload_len = int.from_bytes(message[16:20], "little")
    checksum = message[20:24]
    payload = message[24 : 24 + payload_len]
    if len(message) < 24 or len(payload) != payload_len:
        raise ValueError("Not enough data")
    if checksum != sha256(sha256(payload).digest()).digest()[:4]:
        raise WrongChecksumError("Wrong checksum, the message might have been tampered")
    return True


def get_payload(message: bytes):
    verify_headers(message)
    message_name = message[4:16].rstrip(b"\x00").decode()
    payload_len = int.from_bytes(message[16:20], "little")
    payload = message[24 : 24 + payload_len]
    return (message_name, payload)
