"""
A module for handling audio related input and output stuff.
"""

import threading
import queue
import pyaudio
from incremental import abstract, audio

CHANNELS = 1
"""Number of channels. Should never be changed. As soon as stereo telephony
becomes a thing I will rewrite this."""

TIMEOUT = 0.1

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
        return audio.common.AudioIncrementalUnit


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

    def __init__(self, chunk_size, rate=44100, sample_width=2):
        """
        Initialize the Microphone Module.

        Args:
            chunk_size (int): The number of frames that should be stored in one
                AudioIncrementalUnit
            rate (int): The frame rate of the recording
            sample_width (int): The width of a single sample of audio in bytes.
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
        self.stream = p.open(format=p.get_format_from_width(self.sample_width),
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

class SpeakerModule(abstract.AbstractConsumingModule):
    """A module that produces IUs containing audio signals that are captures by
    a microphone."""

    @staticmethod
    def name():
        return "Speaker Module"

    @staticmethod
    def description():
        return "A consuming module that plays audio from speakers."

    @staticmethod
    def input_ius():
        return [audio.AudioIncrementalUnit]

    @staticmethod
    def output_iu():
        return None


    def callback(self, in_data, frame_count, time_info, status):
        """The callback function that gets called by pyaudio."""
        if self.audio_buffer:
            try:
                audio_paket = b''
                while len(audio_paket) != frame_count*self.s_width_bytes:
                    audio_paket += self.audio_buffer.get(timeout=TIMEOUT)
                return (audio_paket, pyaudio.paContinue)
            except queue.Empty:
                pass
        print("FRAME DROP")
        return (b'0'*frame_count*self.s_width_bytes, pyaudio.paContinue)

    def __init__(self, chunk_size, rate=44100, sample_width=2):
        super().__init__()
        self.chunk_size = chunk_size
        self.rate = rate
        self.sample_width = sample_width

        self._p = pyaudio.PyAudio()

        self.audio_buffer = queue.Queue()
        self._aside_buffer = b''
        self._frame_counter = 0
        self.stream = None

    def process_iu(self, input_iu):
        self.audio_buffer.put(input_iu.raw_audio)
        return None

    def setup(self):
        """Set up the speaker for speaking...?"""
        p = self._p
        self.stream = p.open(format=p.get_format_from_width(self.sample_width),
                             channels=CHANNELS,
                             rate=self.rate,
                             input=False,
                             output=True,
                             stream_callback=self.callback,
                             frames_per_buffer=self.chunk_size)
        self.stream.start_stream()

    def shutdown(self):
        """Close the audio stream."""
        self.stream.stop_stream()
        self.stream.close()
        self.stream = None
        self.audio_buffer = []
