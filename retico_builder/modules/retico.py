"""A module containing all retico module widgets. This includes all audio
modules relying on pyaudio."""

from retico_builder.modules.abstract import InfoLabelWidget, ModuleWidget

from retico.core.debug.general import CallbackModule
from retico.core.audio import io


class DebugModuleWidget(InfoLabelWidget):
    """A debug module widget utilizing the CallbackModule of retico."""
    retico_class = CallbackModule

    def callback(self, input_iu):
        self.info_label.text = str(input_iu.payload)

    def __init__(self, **kwargs):
        del kwargs["retico_args"]
        del kwargs["show_popup"]
        super().__init__(retico_args={"callback": self.callback},
                         show_popup=False,
                         **kwargs)

    def get_args(self):
        return {}

class SpeakerModuleWidget(ModuleWidget):
    """A speaker module."""

    retico_class = io.SpeakerModule


class MicrophoneModuleWidget(ModuleWidget):
    """A microphone module."""

    retico_class = io.MicrophoneModule
    args = {"chunk_size": 5000}


class AudioRecorderModuleWidget(InfoLabelWidget):
    """An audio recorder module."""

    retico_class = io.AudioRecorderModule
    args = {"filename": "recording.wav"}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.info_label.text = "Saving to file: %s" % self.args["filename"]

    def popup_callback(self, instance):
        super().popup_callback(instance)
        self.info_label.text = "Saving to file: %s" % self.args["filename"]


class AudioDispatcherModuleWidget(ModuleWidget):
    """An audio dispatcher module."""

    retico_class = io.AudioDispatcherModule
    args = {"target_chunk_size": 5000}
