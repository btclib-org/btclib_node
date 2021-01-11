import enum

ProtocolVersion = 70015


class P2pConnStatus(enum.IntEnum):
    Open = 1
    Connected = 2
    Closed = 3


class NodeStatus(enum.IntEnum):
    Starting = 1
    SyncingHeaders = 2
    HeaderSynced = 3
    Reindexing = 4
    BlockSynced = 5
