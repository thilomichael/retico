"""Module for simulated natural language understanding."""

from retico.core import abstract
from retico.core.text.common import SpeechRecognitionIU
from retico.core.dialogue.common import DialogueActIU


class SimulatedNLUModule(abstract.AbstractModule):
    """A Simulated NLU Module that takes SpeechRecognitionIUs and produces
    dialogue acts."""

    @staticmethod
    def name():
        return "Simulated NLU Module"

    @staticmethod
    def description():
        return ("A Module that produces dialogue acts from the meta data of"
                "SpeechRecognitionIUs from the SimulatedASRModule")

    @staticmethod
    def input_ius():
        return [SpeechRecognitionIU]

    @staticmethod
    def output_iu():
        return DialogueActIU

    def process_iu(self, input_iu):
        output_iu = self.create_iu(input_iu)
        output_iu.set_act(input_iu.meta_data["dialogue_act"],
                          input_iu.meta_data["concepts"])
        return output_iu
