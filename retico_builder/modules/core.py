from flexx import flx
from retico_builder.modules.abstract import AbstractModule

from retico.core.audio import io
from retico.core.text import asr

class AudioRecorderModule(AbstractModule):

    MODULE = io.AudioRecorderModule
    PARAMETERS = {"filename": "recorded_audio.wav", "rate": 44100, "sample_width": 2}

    def set_content(self):
        self.gui.clear_content()
        self.gui.add_info("Filename: %s" % self.retico_module.filename)
        self.gui.add_info("Rate: %d" % self.retico_module.rate)
        self.gui.add_info("Sample Width: %d" % self.retico_module.sample_width)

class AudioDispatcherModule(AbstractModule):

    MODULE = io.AudioDispatcherModule
    PARAMETERS = {"target_chunk_size": 5000, "rate": 44100, "sample_width": 2,
                 "speed": 1.0, "continuous": True, "silence": None}

    def set_content(self):
        self.gui.clear_content()
        self.gui.add_info("Target chunk size: %d" % self.retico_module.target_chunk_size)
        self.gui.add_info("Rate: %d" % self.retico_module.rate)
        self.gui.add_info("Sample Width: %d" % self.retico_module.sample_width)
        self.gui.add_info("Speed: %d" % self.retico_module.speed)
        self.gui.add_info("Continuous: %s" % self.retico_module.continuous)
        self.gui.add_info("Silence: %d" % len(self.retico_module.silence))

class SpeakerModule(AbstractModule):

    MODULE = io.SpeakerModule
    PARAMETERS = {"rate": 44100, "sample_width": 2, "use_speaker": "both"}

    def set_content(self):
        self.gui.clear_content()
        self.gui.add_info("Rate: %d" % self.retico_module.rate)
        self.gui.add_info("Sample Width: %d" % self.retico_module.sample_width)
        self.gui.add_info("Using Speaker: %s" % self.retico_module.use_speaker)

class StreamingSpeakerModule(AbstractModule):

    MODULE = io.StreamingSpeakerModule
    PARAMETERS = {"chunk_size": 5000, "rate": 44100, "sample_width": 2}

    def set_content(self):
        self.gui.clear_content()
        self.gui.add_info("Chunk Size: %d" % self.retico_module.chunk_size)
        self.gui.add_info("Rate: %d" % self.retico_module.rate)
        self.gui.add_info("Sample Width: %d" % self.retico_module.sample_width)

class MicrophoneModule(AbstractModule):

    MODULE = io.MicrophoneModule
    PARAMETERS = {"chunk_size": 5000, "rate": 44100, "sample_width": 2}

    def set_content(self):
        self.gui.clear_content()
        self.gui.add_info("Chunk Size: %d" % self.retico_module.chunk_size)
        self.gui.add_info("Rate: %d" % self.retico_module.rate)
        self.gui.add_info("Sample Width: %d" % self.retico_module.sample_width)

class TextDispatcherModule(AbstractModule):

    MODULE = asr.TextDispatcherModule
    PARAMETERS = {"forward_after_final": True}

    def set_content(self):
        self.gui.clear_content()
        self.gui.add_info("Text Dispatcher Module")

    def update_running_info(self):
        latest_iu = self.retico_module.latest_iu()
        if latest_iu:
            self.gui.update_info("Current text:<br>%s" % latest_iu.payload)

class IncrementalizeASRModule(AbstractModule):

    MODULE = asr.IncrementalizeASRModule
    PARAMETERS = {"threshold": 0.8}

    def set_content(self):
        self.gui.clear_content()
        self.gui.add_info("Incrementalize ASR Module")

    def update_running_info(self):
        latest_iu = self.retico_module.latest_iu()
        if latest_iu:
            self.gui.update_info("Current text:<br>%s" % latest_iu.payload)
