from dataclasses import dataclass
from pathlib import Path

from btclib_node.chains import Chain, Main, RegTest, SigNet, TestNet


@dataclass
class Config:
    chain: Chain
    data_dir: str
    p2p_port: int
    rpc_port: int
    pruned: bool
    debug: bool

    def __init__(
        self,
        chain=Main(),
        data_dir=None,
        p2p_port=None,
        rpc_port=None,
        allow_p2p=True,
        allow_rpc=True,
        pruned=False,
        debug=False,
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

        data_dir = Path(data_dir) if data_dir else Path.home() / ".btclib"
        self.data_dir = data_dir.absolute() / self.chain.name

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

        self.debug = debug
