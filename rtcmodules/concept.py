"""
This module defines the information units concerning abstract concepts.
"""
from rtcmodules import abstract


class DialogueActIncrementalUnit(abstract.IncrementalUnit):
    """A Dialog Act Incremental Unit.

    This IU represents a Dialogue Act together with concepts and their
    values. In this implementation only a single act can be expressed with a
    single IU.

    Attributes:
        act (string): A representation of the current act as a string.
        concepts (dict): A dictionary of names of concepts being mapped on to
            their actual values.
    """

    @staticmethod
    def type():
        return "Concept Incremental Unit"

    def __init__(self, creator, iuid=0, previous_iu=None, grounded_in=None,
                 payload=None, act=None, concepts=None):
        """Initialize the DialogueActIncrementalUnit with act and concepts.

        Args:
            act (string): A representation of the act.
            concepts (dict): A representation of the concepts as a dictionary.
        """
        super().__init__(creator, iuid=iuid, previous_iu=previous_iu,
                         grounded_in=grounded_in, payload=payload)
        self.act = act
        self.concepts = {}
        if concepts:
            self.concepts = concepts

    def set_act(self, act, concepts=None):
        """Set the act and concept of the IU.

        Old acts or concepts will be overwritten.

        Args:
            act (string): The act of the IU as a string.
            concepts (dict): A dictionary containing the new concepts.
        """
        self.act = act
        if concepts:
            self.concepts = concepts
