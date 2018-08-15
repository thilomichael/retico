"""
A module that helps transforming text to be used for synthesis.
"""

from retico.core import abstract, text
class ASRtoTTSModule(abstract.AbstractModule):

    @staticmethod
    def name():
        return "ASR to TTS Module"

    @staticmethod
    def description():
        return "A module that uses SpeechRecognition IUs and outputs dispatchable IUs"

    @staticmethod
    def input_ius():
        return [text.common.SpeechRecognitionIU]

    @staticmethod
    def output_iu():
        return text.common.GeneratedTextIU

    def process_iu(self, input_iu):
        if input_iu.final:
            output_iu = self.create_iu(input_iu)
            output_iu.payload = input_iu.get_text()
            output_iu.dispatch = True
            return output_iu