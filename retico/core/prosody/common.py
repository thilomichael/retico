"""
This module defines the common structures for prosody analysis used for the
dialogue management.
One example being an end-of-turn prediction.
"""

from retico.core import abstract


class EndOfTurnIU(abstract.IncrementalUnit):
    """An incremental unit used for prediction of the end of the turn. This
    information may be used by a dialogue management module to plan next turns
    and enabling realistic turn taking.
    """

    @staticmethod
    def type():
        return "End-of-Turn Incremental Unit"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.probability = 0.0
        self.is_speaking = False

    def set_eot(self, probability=0.0, is_speaking=False):
        """Set the end-of-turn probability and a flag if the interlocutor is
        currently speaking (VAD).

        Args:
            probability (float): The probability that the turn is ending.
            is_speaking (bool): Whether or not the interlocutor is speaking.
        """
        self.is_speaking = is_speaking
        self.probability = probability
