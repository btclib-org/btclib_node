import os


class BlockDB:
    def __init__(self, data_dir):
        data_dir = os.path.join(data_dir, "blocks")
        os.makedirs(data_dir, exist_ok=True)

        # self.data = {}
        self.count = 0

    # TODO: store on disk
    def add_block(self, block):
        self.count += 1
        # self.data[block.header.hash] = block

    def get_block(self, hash):
        pass
        # return self.data[hash]
