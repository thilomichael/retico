"""
A network module that may apply different types of degradations.
"""

from retico.core.abstract import AbstractModule
from retico.core.audio.common import DispatchedAudioIU
from retico.modules.net.degradations import Delay

class NetworkModule(AbstractModule):
    """A network module that takes Audio IUs, adds degradations to them and
    outputs them."""

    @staticmethod
    def name():
        return "Network Module"

    @staticmethod
    def description():
        return "A Module that applies degradations to Audio IUs"

    @staticmethod
    def input_ius():
        return [DispatchedAudioIU]

    @staticmethod
    def output_iu():
        return DispatchedAudioIU

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.degradations = []

    def add_degradation(self, degradation):
        """Append a degradation to the list of applied degradations

        Args:
            degradation (Degradation): A degradation to be applied
        """
        self.degradations.append(degradation)

    def clear_degradations(self):
        """Remove all degradation from the network."""
        self.degradations = []

    def process_iu(self, input_iu):
        output_iu = self.create_iu(input_iu)
        output_iu.set_audio(input_iu.raw_audio,
                            input_iu.nframes,
                            input_iu.rate,
                            input_iu.sample_width)
        output_iu.set_dispatching(input_iu.completion, input_iu.is_dispatching)
        for degradation in self.degradations:
            degradation.degrade(output_iu, input_iu)
        self.append(output_iu)

class DelayedNetworkModule(NetworkModule):
    @staticmethod
    def name():
        return "Delayed Network Module"


    @staticmethod
    def description():
        return "A Module that applies delay to Audio IUs"

    def __init__(self, delay, **kwargs):
        super().__init__(**kwargs)
        self.delay = delay

    def setup(self):
        delay = Delay(self.delay)
        self.add_degradation(delay)

    def shutdown(self):
        self.clear_degradations()