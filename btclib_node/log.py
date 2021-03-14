import logging


class Logger(logging.Logger):
    def __init__(self, filepath=None, debug=False, **kwargs):
        super().__init__(name="Logger", level=logging.DEBUG, **kwargs)
        if debug:
            handler = logging.StreamHandler()
        else:
            handler = logging.FileHandler(filepath)
        formatter = logging.Formatter("%(asctime)s - %(message)s")
        handler.setFormatter(formatter)
        self.addHandler(handler)

    def close(self):
        for handler in self.handlers:
            handler.close()
            self.removeHandler(handler)
