import enum

ProtocolVersion = 70015
P2pConnStatus = enum.IntEnum("P2pConnStatus", ["Open", "Connected", "Closed"])

NodeStatus = enum.IntEnum(
    "NodeStatus",
    ["Starting", "SyncingHeaders", "HeaderSynced", "Reindexing", "BlockSynced"],
)
