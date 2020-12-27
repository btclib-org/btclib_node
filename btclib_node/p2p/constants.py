import enum

ProtocolVersion = 70015
ConnectionStatus = enum.IntEnum(
    "ConnectionStatus", ["Open", "Version", "Connected", "Closed"]
)
