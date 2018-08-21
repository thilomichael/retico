from retico.core.abstract import AbstractConsumingModule

from retico.core.text.common import TextIU, GeneratedTextIU, SpeechRecognitionIU

class TextRecorderModule(AbstractConsumingModule):
    """A module that writes the received text into a file."""

    @staticmethod
    def name():
        return "Text Recorder Module"

    @staticmethod
    def description():
        return "A module that writes received TextIUs to file"

    @staticmethod
    def input_ius():
        return [TextIU, GeneratedTextIU, SpeechRecognitionIU]

    def process_iu(self, input_iu):
        pass