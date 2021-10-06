"""
A module of degradations for a network.
"""

import time
import random


class Degradation:
    """An abstract degradation class"""

    @staticmethod
    def name():
        """Return the human-readable name of the degradation.

        Returns:
            str: The human-readable name of degradation.

        """
        raise NotImplementedError

    def degrade(self, iu, original_iu):
        """Degrade the given iu and returns it in degraded format.

        This method may modify the input iu. It does not have to create a copy.

        Args:
            iu (IncrementalUnit): The IU to be degraded
            original_iu (IncrementalUnit): The original IU

        Returns:
             IncrementalUnit: The degraded Incremental Unit

        """
        raise NotImplementedError


class Delay(Degradation):
    """A delay degradation that waits for a specified amount of time before returning
    the IU - effectively delaying the submission of the packet."""

    @staticmethod
    def name():
        return "Delay"

    def __init__(self, delay):
        """Initialize the Degradation with the given delay in seconds

        Args:
            delay (float): Delay in seconds
        """
        self.delay = delay

    def degrade(self, iu, original_iu):
        d = self.delay - original_iu.age()
        iu.meta_data["delay"] = d  # Add delay as meta data to IU
        if d > 0:
            time.sleep(d)
        return iu


class PacketLoss(Degradation):
    """A packet loss degradation that overwrites the content of the IU with zeros.
    The packet-loss is decided by a two-state markov chain as described in:

        - Narrowband E-model (ITU-T G.107)
        - Raake et al. 2006 - Short- and Long-Term Packet Loss Behavior"""

    LOST_STATE = 1
    """The markov chain state denoting the packet was lost."""
    FOUND_STATE = 0
    """The markov chain state denoting the packet was found (i.e., not lost)."""

    @staticmethod
    def name():
        "Packet loss"

    def __init__(self, ppl, burstr):
        """Initialize the Degradation with the gvien packet loss probability (ppl) and
        burst ratio (burstr).

        Args:
            ppl (float): The overall packet loss probability ranging from 0.0 to 1.0
            burstr (float): The burst ratio with 1.0 being uniformly distributed
        """
        self.set_packetloss(ppl, burstr)
        self.pl_state = self.FOUND_STATE  # Initially we are always in found state

    def set_packetloss(self, ppl, burstr):
        """Sets the packet loss and burst ratio of the Degradation. This updates
        internal variables.
        """
        self._ppl = ppl
        self._burstr = burstr

        # Calculating p and q from the two-state markov chain
        self._q = (1 - ppl) / burstr  # transition probability from "lost" to "found"
        self._p = (ppl * self._q) / (1 - ppl)  # transition from "found" to "lost"

    def determine_packetloss(self):
        """Calculates the new packet loss state based on the p and q values (i.e. on ppl
        and burstr) and returns the new packet loss state.

        Returns:
            int: The new packet loss state with 0 indicating found and 1 indicating lost
        """
        if self.pl_state == self.FOUND_STATE:  # Found state
            if random.random() < self._p:
                self.pl_state = 1
        elif self.pl_state == self.LOST_STATE:  # Lost state
            if random.random() < self._q:
                self.pl_state = 0
        return self.pl_state

    def degrade(self, iu, original_iu):
        # Calculate new PL state
        if self.determine_packetloss() == self.LOST_STATE:
            # PL
            iu.meta_data["packet-loss"] = True
            iu.raw_audio = ("\x00" * len(iu.raw_audio)).encode()
        else:
            # NO PL
            iu.meta_data["packet-loss"] = False
        iu.meta_data["ppl"] = self._ppl
        iu.meta_data["burstr"] = self._burstr
        return iu
