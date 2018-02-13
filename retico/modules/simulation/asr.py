"""
A module for Real Time Conversation Modules that use meta-data provided by
previous module and have no real functionality. This way different module may
be abstracted.

The simulation.asr module tries to mimic real automatic speech recognition
modules by taking in audio and producing text.
"""

from retico.core import abstract
from retico.core.text.common import SpeechRecognitionIU
from retico.core.audio.common import DispatchedAudioIU


class SimulatedASRModule(abstract.AbstractModule):
    """A simulated ASR module that tries to mimic a real ASR module by reading
    meta data.

    This module tries to output the text of the incoming audio only in part.
    For this it uses the "completion" meta-data to approximate the current
    position in the utterance.
    """

    @staticmethod
    def name():
        return "Simulated ASR Module"

    @staticmethod
    def description():
        return "An Module that mimics a real incremental ASR module."

    @staticmethod
    def output_iu():
        return SpeechRecognitionIU

    @staticmethod
    def input_ius():
        return [DispatchedAudioIU]

    def process_iu(self, input_iu):
        # output_iu = self.create_iu(input_iu)
        transcription = input_iu.meta_data.get("transcription")
        if transcription:
            completion = input_iu.completion

            # Calculating the current text by only taking [completion] % of the
            # whole text
            ts = transcription.split(" ")
            cur_trans = ts[0:int(len(ts) * completion) + 1]
            cur_trans = " ".join(cur_trans)

            output_iu = self.create_iu(input_iu)
            output_iu.set_asr_results([cur_trans], cur_trans, completion, 1,
                                      completion == 1)
            return output_iu
