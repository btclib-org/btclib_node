import enum

ProtocolVersion = 70015
P2pConnectionStatus = enum.IntEnum(
    "P2pConnectionStatus", ["Open", "Version", "Connected", "Closed"]
)
