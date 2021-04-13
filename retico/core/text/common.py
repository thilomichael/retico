"""
This module redefines the abstract classes to fit the needs of automatic speech
recognizer.
"""

from retico.core import abstract


class TextIU(abstract.IncrementalUnit):
    """An IU that contains text."""

    @staticmethod
    def type():
        return "Text IU"

    def get_text(self):
        """Return the text contained in the IU.

        Returns:
            str: The text contained in the IU.
        """
        return self.payload


class GeneratedTextIU(TextIU):
    """An IU that contains generated text.

    This includes information about whether the text should be dispatched once
    it has been transformed into speech."""

    @staticmethod
    def type():
        return "Generated Text IU"

    def __init__(self, dispatch=False, **kwargs):
        super().__init__(**kwargs)
        self.dispatch = dispatch


class SpeechRecognitionIU(TextIU):
    """An IU that contains information about recognized speech."""

    @staticmethod
    def type():
        return "Speech Recgonition IU"

    def __init__(
        self, creator, iuid=0, previous_iu=None, grounded_in=None, payload=None
    ):
        super().__init__(
            creator,
            iuid=iuid,
            previous_iu=previous_iu,
            grounded_in=grounded_in,
            payload=payload,
        )
        self.predictions = None
        self.stability = None
        self.confidence = None
        self.payload = payload
        self.text = None
        self.final = False

    def set_asr_results(self, predictions, text, stability, confidence, final):
        """Set the asr results for the SpeechRecognitionIU.

        Args:
            predictions (list): A list of predictions. This will also set the
                payload. The last prediction in this list should be the latest
                and best prediction.
            text (str): The text of the latest prediction
            stability (float): The stability of the latest prediction
            confidence (float): The confidence in the latest prediction
            final (boolean): Whether the prediction is final
        """
        self.predictions = predictions
        self.payload = predictions
        self.text = text
        self.stability = stability
        self.confidence = confidence
        self.final = final

    def get_text(self):
        return self.text
