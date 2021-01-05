import os


class BlockDB:
    def __init__(self, data_dir):
        data_dir = os.path.join(data_dir, "blocks")
        os.makedirs(data_dir, exist_ok=True)

        self.data = {}

    # TODO: store on disk
    def add_block(self, block):
        self.data[block.header.hash] = block

    def get_block(self, hash):
        return self.data[hash]
