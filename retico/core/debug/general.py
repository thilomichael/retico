"""A module for general debug modules."""

from retico.core import abstract


class CallbackModule(abstract.AbstractConsumingModule):
    """A debug module that returns the incoming IUs into a callback function."""

    @staticmethod
    def name():
        return "Callback Debug Module"

    @staticmethod
    def description():
        return ("A consuming module that calls a callback function whenever an"
                "IU arrives.")

    @staticmethod
    def input_ius():
        return [abstract.IncrementalUnit]

    def __init__(self, callback, **kwargs):
        super().__init__(**kwargs)
        self.callback = callback

    def process_iu(self, input_iu):
        self.callback(input_iu)
