"""
This module handles input and output of text.
"""

from retico.core.abstract import AbstractConsumingModule
from retico.core.abstract import AbstractTriggerModule
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

    def __init__(self, filename, separator="\t", **kwargs):
        super().__init__(**kwargs)
        self.filename = filename
        self.separator = separator
        self.txt_file = None

    def setup(self):
        self.txt_file = open(self.filename, "w")

    def shutdown(self):
        if self.txt_file:
            self.txt_file.close()
            self.txt_file = None

    def process_iu(self, input_iu):
        if self.txt_file:
            self.txt_file.write(str(input_iu.grounded_in.creator))
            self.txt_file.write(self.separator)
            self.txt_file.write(str(input_iu.created_at))
            self.txt_file.write(self.separator)
            self.txt_file.write(input_iu.get_text())
            if isinstance(input_iu, GeneratedTextIU):
                self.txt_file.write(self.separator)
                self.txt_file.write(str(input_iu.dispatch))
            if isinstance(input_iu, SpeechRecognitionIU):
                self.txt_file.write(self.separator)
                self.txt_file.write(str(input_iu.predictions))
                self.txt_file.write(self.separator)
                self.txt_file.write(str(input_iu.stability))
                self.txt_file.write(self.separator)
                self.txt_file.write(str(input_iu.confidence))
                self.txt_file.write(self.separator)
                self.txt_file.write(str(input_iu.final))
            self.txt_file.write("\n")

class TextTriggerModule(AbstractTriggerModule):

    @staticmethod
    def name():
        return "Text Trigger Module"

    @staticmethod
    def description():
        return "A trigger module that creates a TextIU once its triggered"

    @staticmethod
    def output_iu():
        return GeneratedTextIU

    def __init__(self, dispatch=True, **kwargs):
        super().__init__(**kwargs)
        self.dispatch=dispatch

    def trigger(self, data={}):
        text = data.get("text", "This is a trigger test")
        output_iu = self.create_iu()
        output_iu.payload = text
        output_iu.dispatch = self.dispatch
        self.append(output_iu)
