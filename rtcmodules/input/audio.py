"""
A module for Audio Modules that have no input IUs because they get their inputs
from somewhere else. These module take in audio from some kind of source and
produce IUs containing the audio information.
"""

import threading
import pyaudio
from rtcmodules import abstract, audio

CHANNELS = 1
"""Number of channels. Should never be changed. As soon as stereo telephony
becomes a thing I will rewrite this."""

class MicrophoneModule(abstract.AbstractProducingModule):
    """A module that produces IUs containing audio signals that are captures by
    a microphone."""

    @staticmethod
    def name():
        return "Microphone Module"

    @staticmethod
    def description():
        return "A prodicing module that records audio from microphone."

    @staticmethod
    def input_ius():
        return []

    @staticmethod
    def output_iu():
        return audio.AudioIncrementalUnit


    def callback(self, in_data, frame_count, time_info, status):
        """The callback function that gets called by pyaudio.

        Args:
            in_data (bytes[]): The raw audio that is coming in from the
                microphone
            frame_count (int): The number of frames that are stored in in_data
        """
        with self.audio_mutex:
            self.audio_buffer.append(in_data)
        return (in_data, pyaudio.paContinue)

    def __init__(self, chunk_size, rate=44100, sample_width=16):
        """
        Initialize the Microphone Module.

        Args:
            chunk_size (int): The number of frames that should be stored in one
                AudioIncrementalUnit
            rate (int): The frame rate of the recording
            sample_width (int): The width of a single sample of audio in bits.
        """
        super().__init__()
        self.chunk_size = chunk_size
        self.rate = rate
        self.sample_width = sample_width

        self._p = pyaudio.PyAudio()

        self.audio_mutex = threading.Lock()
        self.audio_buffer = []
        self.stream = None

    def process_iu(self, input_iu):
        with self.audio_mutex:
            if not self.audio_buffer:
                return None
            sample = self.audio_buffer.pop(0)
            output_iu = self.create_iu()
            output_iu.set_audio(sample, self.chunk_size, self.rate,
                                self.sample_width)
            return output_iu

    def setup(self):
        """Set up the microphone for recording."""
        p = self._p
        sample_width_bytes = self.sample_width / 8
        self.stream = p.open(format=p.get_format_from_width(sample_width_bytes),
                             channels=CHANNELS,
                             rate=self.rate,
                             input=True,
                             output=False,
                             stream_callback=self.callback,
                             frames_per_buffer=self.chunk_size)
        self.stream.start_stream()

    def shutdown(self):
        """Close the audio stream."""
        with self.audio_mutex:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
            self.audio_buffer = []
