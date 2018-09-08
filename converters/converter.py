"""Base classes for converters package"""


class Converter:
    """ Abstract converter """
    def __init__(self, source, target):
        self.source = source
        self.target = target

    def convert(self):
        raise NotImplementedError()

    def transfer(self):
        raise NotImplementedError()