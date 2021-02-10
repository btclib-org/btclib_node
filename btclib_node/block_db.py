from btclib.blocks import Block


class BlockDB:
    def __init__(self, data_dir):
        data_dir = data_dir / "blocks"
        data_dir.mkdir(exist_ok=True, parents=True)

        # self.data = {}

    # TODO: store on disk
    def add_block(self, block):
        pass
        # self.data[block.header.hash] = block

    def get_block(self, hash):
        pass
        # return self.data[hash]
