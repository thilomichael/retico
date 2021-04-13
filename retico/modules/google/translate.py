"""
A module that utilizes Google Translate to translate text between different languages.
"""

from googletrans import Translator
from retico.core import abstract, text


class GoogleTranslateModule(abstract.AbstractModule):
    """A module that translates text."""

    @staticmethod
    def name():
        return "Google Translate Module"

    @staticmethod
    def description():
        return "A Module that incrementally translates text."

    @staticmethod
    def input_ius():
        return [text.common.TextIU]

    @staticmethod
    def output_iu():
        return text.common.TextIU

    def __init__(self, source="de", destination="en", **kwargs):
        """Initialize the GoogleTranslateModule with the given arguments.

        Args:
            source (str): The language code for the source language.
            destination (str): The language code for the destination language
        """
        super().__init__(**kwargs)
        self.source = "de"
        self.destination = "en"
        self.translator = None

    def setup(self):
        self.translator = Translator()

    def process_iu(self, input_iu):
        to_translate = input_iu.get_text()
        if self.translator is not None:
            t = self.translator.translate(
                to_translate, src=self.source, dest=self.destination
            )
            if t.text is not None:
                output_iu = self.create_iu(input_iu)
                output_iu.payload = t.text
                return output_iu

    def shutdown(self):
        self.translator = None
