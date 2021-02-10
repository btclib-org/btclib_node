import logging


class Logger(logging.Logger):
    def __init__(self, filepath, debug=False, **kwargs):
        super().__init__(name="Logger", level=logging.DEBUG, **kwargs)
        self.addHandler(logging.FileHandler(filepath))
        if debug:
            self.addHandler(logging.StreamHandler())
