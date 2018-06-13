from flexx import flx
from retico_builder.modules.abstract import AbstractModule

from retico.core.audio import io

class AudioDispatcherModule(AbstractModule):

    MODULE = io.AudioDispatcherModule
    PARAMETERS = {"target_chunk_size": 5000, "rate": 44100, "sample_width": 2,
                 "speed": 1.0, "continuous": True, "silence": None}

    def get_content(self):
        style = "font-size: 10pt; text-align: center;"
        return [flx.Label(style=style, text="Target chunk size: %d" % self.retico_module.target_chunk_size),
                flx.Label(style=style, text="Rate: %d" % self.retico_module.rate),
                flx.Label(style=style, text="Sample Width: %d" % self.retico_module.sample_width),
                flx.Label(style=style, text="Speed: %d" % self.retico_module.speed),
                flx.Label(style=style, text="Continuous: %s" % self.retico_module.continuous),
                flx.Label(style=style, text="Silence: %d" % len(self.retico_module.silence))]

class SpeakerModule(AbstractModule):

    MODULE = io.SpeakerModule
    PARAMETERS = {"rate": 44100, "sample_width": 2, "use_speaker": "both"}

    def get_content(self):
        style = "font-size: 10pt; text-align: center;"
        return [flx.Label(style=style, text="Rate: %d" % self.retico_module.rate),
                flx.Label(style=style, text="Sample Width: %d" % self.retico_module.sample_width),
                flx.Label(style=style, text="Using Speaker: %s" % self.retico_module.use_speaker)]

class StreamingSpeakerModule(AbstractModule):

    MODULE = io.StreamingSpeakerModule
    PARAMETERS = {"chunk_size": 5000, "rate": 44100, "sample_width": 2}

    def get_content(self):
        style = "font-size: 10pt; text-align: center;"
        return [flx.Label(style=style, text="Chunk Size: %d" % self.retico_module.chunk_size),
                flx.Label(style=style, text="Rate: %d" % self.retico_module.rate),
                flx.Label(style=style, text="Sample Width: %d" % self.retico_module.sample_width)]

class MicrophoneModule(AbstractModule):

    MODULE = io.MicrophoneModule
    PARAMETERS = {"chunk_size": 5000, "rate": 44100, "sample_width": 2}

    def get_content(self):
        style = "font-size: 10pt; text-align: center;"
        return [flx.Label(style=style, text="Chunk Size: %d" % self.retico_module.chunk_size),
                flx.Label(style=style, text="Rate: %d" % self.retico_module.rate),
                flx.Label(style=style, text="Sample Width: %d" % self.retico_module.sample_width)]
