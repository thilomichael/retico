"""
Imposter Text to Speech
"""

from rtcmodules import abstract, speech, audio

class ImposterTTSModule(abstract.AbstractModule):
    """An Imposter TTS Module that uses meta information of incoming IUs to
    output the audio."""

    @staticmethod
    def name():
        return "Imposter TTS Module"

    @staticmethod
    def description():
        return ("A module that uses the meta data to determine the text of the"
                " speech that is produced.")

    @staticmethod
    def input_ius():
        return [speech.TextIU]

    @staticmethod
    def output_iu():
        return audio.AudioIncrementalUnit

    def process_iu(self, input_iu):
        output_iu = self.create_iu(input_iu)
        raw_audio = output_iu.meta_data["raw_audio"]
        rate = output_iu.meta_data["rate"]
        sample_width = output_iu.meta_data["sample_width"]
        nframes = len(raw_audio)/sample_width
        output_iu.set_audio(raw_audio, nframes, rate, sample_width)
        return output_iu
