"""A module for debug output to the console."""

from retico.core import abstract


class DebugModule(abstract.AbstractConsumingModule):
    """A debug module that prints the IUs that are coming in."""

    @staticmethod
    def name():
        return "Debug Module"

    @staticmethod
    def description():
        return "A consuming module that displays IU infos in the console."

    @staticmethod
    def input_ius():
        return [abstract.IncrementalUnit]

    def process_iu(self, input_iu):
        print("Debug:", input_iu)
        print("  PreviousIU:", input_iu.previous_iu)
        print("  GroundedInIU:", input_iu.grounded_in)
        print("  Age:", input_iu.age())
