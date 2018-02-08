"""
A module for Real Time Conversation Modules that use meta-data provided by
previous module and have no real functionality. This way different module may
be abstracted.

The module tries to mimic real natural language generation modules
by taking in dialogue acts and concepts and producing a text.
"""

import random

from retico import abstract
from retico.text.common import GeneratedTextIU
from retico.dialogue.common import DispatchableActIU
from database.simulation import SimulatioDB


class SimulatedNLGModule(abstract.AbstractModule):
    """A simulated NLG module that uses meta information provided inside the
    incoming IUs to generate a natural language text out of dialogue acts.
    """

    @staticmethod
    def name():
        return "Simulated NLG Module"

    @staticmethod
    def description():
        return "A module that produces text out of meta data of the given IU."

    @staticmethod
    def input_ius():
        return [DispatchableActIU]

    @staticmethod
    def output_iu():
        return GeneratedTextIU

    def __init__(self, data_directory):
        super().__init__()
        self.data_directory = data_directory
        self.db = None

    def process_iu(self, input_iu):
        candidates = self.db.query(input_iu.act, input_iu.concepts)
        candidate = random.choice(candidates)  # Random choice
        output_iu = self.create_iu(input_iu)
        output_iu.payload = candidate.transcription
        output_iu.meta_data = candidate.generate_meta()
        output_iu.dispatch = input_iu.dispatch
        return output_iu

    def setup(self):
        self.db = SimulatioDB(self.data_directory)

    def shutdown(self):
        pass
