"""
A module for Real Time Conversation Modules that use meta-data provided by
previous module and have no real functionality. This way different module may
be abstracted.

The module tries to mimic real natural language generation modules
by taking in dialogue acts and concepts and producing a text.
"""

import random

from retico.core import abstract
from retico.core.text.common import GeneratedTextIU
from retico.core.dialogue.common import DispatchableActIU
from retico.modules.simulation.database.simulation import SimulatioDB


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

    def __init__(self, data_directory, agent_type="caller", **kwargs):
        super().__init__(**kwargs)
        self.data_directory = data_directory
        self.agent_type = agent_type
        self.db = None

    def process_iu(self, input_iu):
        if input_iu.act == "":
            output_iu = self.create_iu(input_iu)
            output_iu.payload = "<silence>"
            output_iu.dispatch = False
            output_iu.meta_data["raw_audio"] = b""
            output_iu.meta_data["frame_rate"] = 44100
            output_iu.meta_data["sample_width"] = 2
            return output_iu
        msg_data = input_iu.meta_data["message_data"].split(":")
        act = msg_data[0]
        concepts = {}
        if len(msg_data) > 1:
            c = msg_data[1].split(",")
            for thing in c:
                concepts[thing] = ""
        candidates = self.db.query(act, concepts)
        if not candidates:
            candidates = self.db.query(input_iu.act, {})
            print("FALLBACK TO ACT:",input_iu.act, input_iu.concepts)
        if not candidates:
            print("NO CANDIDATE", input_iu.act)
            return None
        candidate = random.choice(candidates)  # Random choice
        output_iu = self.create_iu(input_iu)
        output_iu.payload = candidate.transcription
        output_iu.meta_data = candidate.generate_meta()
        output_iu.meta_data["concepts"] = input_iu.concepts
        output_iu.dispatch = input_iu.dispatch
        return output_iu

    def setup(self):
        self.db = SimulatioDB(self.data_directory, self.agent_type)

    def shutdown(self):
        pass
