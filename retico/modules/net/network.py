"""
A network module that may apply different types of degradations.
"""

from retico.core.abstract import AbstractModule
from retico.core.audio.common import DispatchedAudioIU
from retico.modules.net.degradations import Delay, PacketLoss


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
        output_iu.set_audio(
            input_iu.raw_audio, input_iu.nframes, input_iu.rate, input_iu.sample_width
        )
        output_iu.set_dispatching(input_iu.completion, input_iu.is_dispatching)
        for degradation in self.degradations:
            degradation.degrade(output_iu, input_iu)
        self.append(output_iu)


class DelayedNetworkModule(NetworkModule):
    """A network module that delays the audio."""

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


class PacketLossNetworkModule(NetworkModule):
    """A network module that adds zero-insertion packet loss to the audio IUs. This is
    done with a two-state markov model as described by ITU-T G.107.

    Based on the probability and burst ratio given, a number of packets are replaced
    with zeros (silence) and the "lost"-flag in the meta_data of the IU is set to true.
    """

    @staticmethod
    def name():
        return "Packet Loss Network Module"

    @staticmethod
    def description():
        return "A Module that applies zero-insetion packet loss to certain Audio IUs"

    def __init__(self, ppl, burstr, **kwargs):
        super().__init__(**kwargs)
        self.ppl = ppl
        self.burstr = burstr

    def setup(self):
        packetloss = PacketLoss(self.ppl, self.burstr)
        self.add_degradation(packetloss)

    def shutdown(self):
        self.clear_degradations()


class DelayPacketLossNetworkModule(NetworkModule):
    """A network module that adds delay as well as zero insertion packet loss. This
    module combines the functionality of the DelayedNetworkModule and the
    PacketLossNetworkModule.
    """

    @staticmethod
    def name():
        return "Delay and Packet Loss Network Module"

    @staticmethod
    def description():
        return "A Module that applied packet loss and delay to the AudioIUs"

    def __init__(self, delay, ppl, burstr, **kwargs):
        super().__init__(**kwargs)
        self.delay = delay
        self.ppl = ppl
        self.burstr = burstr

    def setup(self):
        packetloss = PacketLoss(self.ppl, self.burstr)
        self.add_degradation(packetloss)
        delay = Delay(self.delay)
        self.add_degradation(delay)

    def shutdown(self):
        self.clear_degradations()
