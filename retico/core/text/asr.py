"""
A module that helps transforming text to be used for synthesis.
"""

from retico.core import abstract, text
from retico.core.prosody.common import EndOfTurnIU


class TextDispatcherModule(abstract.AbstractModule):
    """
    A Moduel that turns SpeechRecognitionIUs or TextIUs into GeneratedTextIUs
    that have the dispatch-flag set.


    """

    @staticmethod
    def name():
        return "ASR to TTS Module"

    @staticmethod
    def description():
        return (
            "A module that uses SpeechRecognition IUs and outputs" + " dispatchable IUs"
        )

    @staticmethod
    def input_ius():
        return [text.common.SpeechRecognitionIU, text.common.TextIU]

    @staticmethod
    def output_iu():
        return text.common.GeneratedTextIU

    def __init__(self, forward_after_final=True, **kwargs):
        super().__init__(**kwargs)
        self.forward_after_final = forward_after_final

    def process_iu(self, input_iu):
        if isinstance(input_iu, text.common.SpeechRecognitionIU):
            if self.forward_after_final and not input_iu.final:
                return
        output_iu = self.create_iu(input_iu)
        output_iu.payload = input_iu.get_text()
        output_iu.dispatch = True
        return output_iu


class IncrementalizeASRModule(abstract.AbstractModule):
    @staticmethod
    def name():
        return "Incrementalize ASR Module"

    @staticmethod
    def description():
        return "A module that takes SpeechRecognitionIUs and emits only the increments from the previous iu"

    @staticmethod
    def input_ius():
        return [text.common.SpeechRecognitionIU]

    @staticmethod
    def output_iu():
        return text.common.SpeechRecognitionIU

    def __init__(self, threshold=0.8, **kwargs):
        super().__init__(**kwargs)
        self.last_ius = []
        self.threshold = threshold

    def get_increment(self, new_text):
        """Compares the full text given by the asr with the IUs that are already
        produced and returns only the increment from the last update. It revokes all
        previously produced IUs that do not match."""
        for iu in self.last_ius:
            if new_text.startswith(iu.text):
                new_text = new_text[len(iu.text) :]
            else:
                iu.revoked = True
        self.last_ius = [iu for iu in self.last_ius if not iu.revoked]
        return new_text

    def process_iu(self, input_iu):
        if input_iu.stability < self.threshold and input_iu.confidence == 0.0:
            return None
        current_text = input_iu.get_text()
        if self.last_ius:
            current_text = self.get_increment(current_text)
        if current_text.strip() == "":
            return None

        output_iu = self.create_iu(input_iu)

        # Just copy the input IU
        output_iu.set_asr_results(
            input_iu.predictions,
            current_text,
            input_iu.stability,
            input_iu.confidence,
            input_iu.final,
        )
        self.last_ius.append(output_iu)

        if output_iu.final:
            self.last_ius = []
            output_iu.committed = True

        return output_iu


class EndOfUtteranceModule(abstract.AbstractModule):
    @staticmethod
    def name():
        return "End of Utterance Module"

    @staticmethod
    def description():
        return "A module that takes forwards the end of utterance from the ASR output"

    @staticmethod
    def input_ius():
        return [text.common.SpeechRecognitionIU]

    @staticmethod
    def output_iu():
        return EndOfTurnIU

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def process_iu(self, input_iu):
        if input_iu.final:
            outiu = self.create_iu(input_iu)
            outiu.set_eot(1.0, False)
            return outiu
