"""
A module of degradations for a network.
"""

import time

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
        # print("sleeping %.2f" % d)
        if d > 0:
            time.sleep(d)
        return iu