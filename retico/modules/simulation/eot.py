"""
A Simulated End-of-Turn predictor module.
"""

from retico.core import abstract
from retico.core.audio.common import DispatchedAudioIU
from retico.core.prosody.common import EndOfTurnIU


class SimulatedEoTModule(abstract.AbstractModule):
    """EoT prediction module."""

    @staticmethod
    def name():
        return "Simulated End-of-Turn Module"

    @staticmethod
    def description():
        return ("A module that uses meta data to give a prediction on when the"
                "turn will be ending")

    @staticmethod
    def input_ius():
        return [DispatchedAudioIU]

    @staticmethod
    def output_iu():
        return EndOfTurnIU

    def process_iu(self, input_iu):
        output_iu = self.create_iu(input_iu)
        output_iu.set_eot(input_iu.completion, input_iu.is_dispatching)
        return output_iu
