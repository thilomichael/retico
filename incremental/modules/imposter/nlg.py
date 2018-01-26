"""
A module for Real Time Conversation Modules that use meta-data provided by
previous module and have no real functionality. This way different module may
be abstracted.

The nlg.imposter module tries to mimic real natural language generation modules
by taking in dialogue acts and concepts and producing a text.
"""

import random

from incremental import abstract, dialogue, speech
from database.imposter import ImposterDB

class ImposterNLGModule(abstract.AbstractModule):
    """An imposter NLG module that uses meta information provided inside the
    incoming IUs to generate a natural language text out of dialogue acts.
    """

    @staticmethod
    def name():
        return "Importer NLG Module"

    @staticmethod
    def description():
        return "A module that produces text but in an imposter kind of way."

    @staticmethod
    def input_ius():
        return [dialogue.common.DialogueActIncrementalUnit]

    @staticmethod
    def output_iu():
        return speech.common.TextIU

    def __init__(self, data_directory):
        self.data_directory = data_directory
        self.db = None

    def process_iu(self, input_iu):
        candidates = self.db.query(input_iu.act, input_iu.concepts)
        candidate = random.choice(candidates)
        output_iu = self.create_iu(input_iu)
        output_iu.payload = candidate.transcription
        output_iu.meta_data = candidate.generate_meta()
        return output_iu

    def setup(self):
        self.db = ImposterDB(self.data_directory)

    def shutdown(self):
        pass
