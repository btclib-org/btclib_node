import os
from dataclasses import dataclass

from btclib_node.chains import Chain, Main, RegTest, SigNet, TestNet


@dataclass
class Config:
    chain: Chain
    data_dir: str
    p2p_port: int
    rpc_port: int
    pruned: bool

    def __init__(
        self,
        chain=Main(),
        data_dir=None,
        p2p_port=None,
        rpc_port=None,
        allow_p2p=True,
        allow_rpc=True,
        pruned=False,
    ):
        if isinstance(chain, Chain):
            self.chain = chain
        elif isinstance(chain, str):
            if chain == "mainnet":
                self.chain = Main()
            elif chain == "testnet":
                self.chain = TestNet()
            elif chain == "signet":
                self.chain = SigNet()
            elif chain == "regtest":
                self.chain = RegTest()
            else:
                raise ValueError
        else:
            raise ValueError

        if not data_dir:
            data_dir = os.path.join(os.path.expanduser("~"), ".btclib")
        if not os.path.isabs(data_dir):
            data_dir = os.path.join(os.getcwd(), data_dir)
        self.data_dir = os.path.join(data_dir, self.chain.name)

        self.p2p_port = None
        if allow_p2p:
            self.p2p_port = self.chain.port
            if p2p_port:
                self.p2p_port = p2p_port

        self.rpc_port = None
        if allow_rpc:
            self.rpc_port = self.chain.port + 1
            if rpc_port:
                self.rpc_port = rpc_port

        self.pruned = pruned
