"""
Simulated Text to Speech
"""

from retico.core import abstract, text, audio


class SimulatedTTSModule(abstract.AbstractModule):
    """A Simulated TTS Module that uses meta information of incoming IUs to
    output the audio."""

    @staticmethod
    def name():
        return "Simulated TTS Module"

    @staticmethod
    def description():
        return ("A module that uses the meta data to determine the text of the"
                " speech that is produced.")

    @staticmethod
    def input_ius():
        return [text.common.GeneratedTextIU]

    @staticmethod
    def output_iu():
        return audio.common.SpeechIU

    def process_iu(self, input_iu):
        output_iu = self.create_iu(input_iu)
        raw_audio = input_iu.meta_data["raw_audio"]
        rate = input_iu.meta_data["frame_rate"]
        sample_width = input_iu.meta_data["sample_width"]
        nframes = len(raw_audio) / sample_width
        output_iu.set_audio(raw_audio, nframes, rate, sample_width)
        output_iu.dispatch = input_iu.dispatch
        return output_iu
