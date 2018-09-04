"""Base classes for converters package"""


class Converter:
    """ Abstract converter """
    def __init__(self, manager):
        self.manager = manager

    @property
    def session(self):
        return self.manager.session

    def convert(self):
        raise NotImplementedError()
