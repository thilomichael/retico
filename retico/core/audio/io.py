"""
A module for handling audio related input and output stuff.
"""

import threading
import queue
import time
import wave
import pyaudio
from retico.core import abstract
from retico.core.audio.common import AudioIU, SpeechIU, DispatchedAudioIU

CHANNELS = 1
"""Number of channels. Should never be changed. As soon as stereo telephony
becomes a thing I will rewrite this."""

TIMEOUT = 0.01


def generate_silence(nsamples, sample_width):
    """Generates [nsamples] samples of silence, each with [sample_width] bytes.

    Args:
        nsamples (int): Length of the silence that should be generated in
            samples.
        sample_width (int): Width of one sample

    Returns:
        bytes: An array of silence with the length [nsamples] * [sample_width]
    """
    # TODO: find a way to generate real silence
    return b"\0" * nsamples * sample_width


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
    def output_iu():
        return AudioIU

    def callback(self, in_data, frame_count, time_info, status):
        """The callback function that gets called by pyaudio.

        Args:
            in_data (bytes[]): The raw audio that is coming in from the
                microphone
            frame_count (int): The number of frames that are stored in in_data
        """
        self.audio_buffer.put(in_data)
        return (in_data, pyaudio.paContinue)

    def __init__(self, chunk_size, rate=44100, sample_width=2, **kwargs):
        """
        Initialize the Microphone Module.

        Args:
            chunk_size (int): The number of frames that should be stored in one
                AudioIU
            rate (int): The frame rate of the recording
            sample_width (int): The width of a single sample of audio in bytes.
        """
        super().__init__(**kwargs)
        self.chunk_size = chunk_size
        self.rate = rate
        self.sample_width = sample_width

        self._p = pyaudio.PyAudio()

        self.audio_buffer = queue.Queue()
        self.stream = None

    def process_iu(self, input_iu):
        if not self.audio_buffer:
            return None
        sample = self.audio_buffer.get()
        output_iu = self.create_iu()
        output_iu.set_audio(sample, self.chunk_size, self.rate, self.sample_width)
        return output_iu

    def setup(self):
        """Set up the microphone for recording."""
        p = self._p
        self.stream = p.open(
            format=p.get_format_from_width(self.sample_width),
            channels=CHANNELS,
            rate=self.rate,
            input=True,
            output=False,
            stream_callback=self.callback,
            frames_per_buffer=self.chunk_size,
            start=False,
        )

    def prepare_run(self):
        if self.stream:
            self.stream.start_stream()

    def shutdown(self):
        """Close the audio stream."""
        self.stream.stop_stream()
        self.stream.close()
        self.stream = None
        self.audio_buffer = queue.Queue()


class SpeakerModule(abstract.AbstractConsumingModule):
    """A module that consumes AudioIUs of arbitrary size and outputs them to the
    speakers of the machine. When a new IU is incoming, the module blocks as
    long as the current IU is being played."""

    @staticmethod
    def name():
        return "Speaker Module"

    @staticmethod
    def description():
        return "A consuming module that plays audio from speakers."

    @staticmethod
    def input_ius():
        return [AudioIU]

    @staticmethod
    def output_iu():
        return None

    def __init__(self, rate=44100, sample_width=2, use_speaker="both", **kwargs):
        super().__init__(**kwargs)
        self.rate = rate
        self.sample_width = sample_width
        self.use_speaker = use_speaker

        self._p = pyaudio.PyAudio()

        self.stream = None
        self.time = None

    def process_iu(self, input_iu):
        self.stream.write(bytes(input_iu.raw_audio))
        return None

    def setup(self):
        """Set up the speaker for speaking...?"""
        p = self._p
        if self.use_speaker == "left":
            stream_info = pyaudio.PaMacCoreStreamInfo(channel_map=(0, -1))
        elif self.use_speaker == "right":
            stream_info = pyaudio.PaMacCoreStreamInfo(channel_map=(-1, 0))
        else:
            stream_info = pyaudio.PaMacCoreStreamInfo(channel_map=(0, 0))

        self.stream = p.open(
            format=p.get_format_from_width(self.sample_width),
            channels=CHANNELS,
            rate=self.rate,
            input=False,
            output_host_api_specific_stream_info=stream_info,
            output=True,
        )

    def shutdown(self):
        """Close the audio stream."""
        self.stream.stop_stream()
        self.stream.close()
        self.stream = None


class StreamingSpeakerModule(abstract.AbstractConsumingModule):
    """A module that consumes Audio IUs and outputs them to the speaker of the
    machine. The audio output is streamed and thus the Audio IUs have to have
    exactly [chunk_size] samples."""

    @staticmethod
    def name():
        return "Streaming Speaker Module"

    @staticmethod
    def description():
        return "A consuming module that plays audio from speakers."

    @staticmethod
    def input_ius():
        return [AudioIU]

    @staticmethod
    def output_iu():
        return None

    def callback(self, in_data, frame_count, time_info, status):
        """The callback function that gets called by pyaudio."""
        if self.audio_buffer:
            try:
                audio_paket = self.audio_buffer.get(timeout=TIMEOUT)
                return (audio_paket, pyaudio.paContinue)
            except queue.Empty:
                pass
        return (b"\0" * frame_count * self.sample_width, pyaudio.paContinue)

    def __init__(self, chunk_size, rate=44100, sample_width=2, **kwargs):
        """Initialize the streaming speaker module.

        Args:
            chunk_size (int): The number of frames a buffer of the output stream
                should have.
            rate (int): The frame rate of the audio. Defaults to 44100.
            sample_width (int): The sample width of the audio. Defaults to 2.
        """
        super().__init__(**kwargs)
        self.chunk_size = chunk_size
        self.rate = rate
        self.sample_width = sample_width

        self._p = pyaudio.PyAudio()

        self.audio_buffer = queue.Queue()
        self.stream = None

    def process_iu(self, input_iu):
        self.audio_buffer.put(input_iu.raw_audio)
        return None

    def setup(self):
        """Set up the speaker for speaking...?"""
        p = self._p
        self.stream = p.open(
            format=p.get_format_from_width(self.sample_width),
            channels=CHANNELS,
            rate=self.rate,
            input=False,
            output=True,
            stream_callback=self.callback,
            frames_per_buffer=self.chunk_size,
        )

    def prepare_run(self):
        self.stream.start_stream()

    def shutdown(self):
        """Close the audio stream."""
        self.stream.stop_stream()
        self.stream.close()
        self.stream = None
        self.audio_buffer = queue.Queue()


class AudioDispatcherModule(abstract.AbstractModule):
    """An Audio module that takes a raw audio stream of arbitrary size and
    outputs AudioIUs with a specific chunk size at the rate it would be produced
    if the audio was being played.

    This could be espacially useful when an agents' TTS module produces an
    utterance, but this utterance should not be transmitted as a whole but in
    an incremental way.

    Attributes:
        target_chunk_size (int): The size of each output IU in samples.
        silence (bytes): A bytes array containing [target_chunk_size] samples
            of silence that is dispatched when [continuous] is True and no input
            IU is dispatched.
        continuous (bool): Whether or not the dispatching should be continuous.
            If True, AudioIUs with "silence" will be disptached if no input IUs
            are being dispatched. If False, no IUs will be produced during
            silence.
        rate (int): The sample rate of the outout and the input IU.
        sample_width (int): The sample with of the output and input IU.
        speed (float): The speed of the dispatching. 1.0 means realtime.
        dispatching_mutex (threading.Lock): The mutex if an input IU is
            currently being dispatched.
        audio_buffer (list): The current audio buffer containing the output IUs
            that are currently dispatched.
        run_loop (bool): Whether or not the dispatching loop is running.
        interrupt (bool): Whether or not incoming IUs interrupt the old
            dispatching
    """

    @staticmethod
    def name():
        return "Audio Dispatching Module"

    @staticmethod
    def description():
        return (
            "A module that transmits audio by splitting it up into" "streamable pakets."
        )

    @staticmethod
    def input_ius():
        return [SpeechIU]

    @staticmethod
    def output_iu():
        return DispatchedAudioIU

    def __init__(
        self,
        target_chunk_size,
        rate=44100,
        sample_width=2,
        speed=1.0,
        continuous=True,
        silence=None,
        interrupt=True,
        **kwargs
    ):
        """Initialize the AudioDispatcherModule with the given arguments.

        Args:
            target_chunk_size (int): The size of each output IU in samples.
            rate (int): The sample rate of the outout and the input IU.
            sample_width (int): The sample with of the output and input IU.
            speed (float): The speed of the dispatching. 1.0 means realtime.
            continuous (bool): Whether or not the dispatching should be
                continuous. If True, AudioIUs with "silence" will be dispatched
                if no input IUs are being dispatched. If False, no IUs will be
                produced during silence.
            silence (bytes): A bytes array containing target_chunk_size samples
                of silence. If this argument is set to None, a default silence
                of all zeros will be set.
            interrupt (boolean): If this flag is set, a new input IU with audio
                to dispatch will stop the current dispatching process. If set to
                False, the "old" dispatching will be finished before the new one
                is started. If the new input IU has the dispatching flag set to
                False, dispatching will always be stopped.
        """
        super().__init__(**kwargs)
        self.target_chunk_size = target_chunk_size
        if not silence:
            self.silence = generate_silence(target_chunk_size, sample_width)
        else:
            self.silence = silence
        self.continuous = continuous
        self.rate = rate
        self.sample_width = sample_width
        self._is_dispatching = False
        self.dispatching_mutex = threading.Lock()
        self.audio_buffer = []
        self.run_loop = False
        self.speed = speed
        self.interrupt = interrupt

    def is_dispatching(self):
        """Return whether or not the audio dispatcher is dispatching a Speech
        IU.

        Returns:
            bool: Whether or not speech is currently dispatched
        """
        with self.dispatching_mutex:
            return self._is_dispatching

    def set_dispatching(self, value):
        """Set the dispatching value of this module in a thread safe way.

        Args:
            value (bool): The new value of the dispatching flag.
        """
        with self.dispatching_mutex:
            self._is_dispatching = value

    def process_iu(self, input_iu):
        cur_width = self.target_chunk_size * self.sample_width
        # If the AudioDispatcherModule is set to intterupt mode or if the
        # incoming IU is set to not dispatch, we stop dispatching and clean the
        # buffer
        if self.interrupt or not input_iu.dispatch:
            self.set_dispatching(False)
            self.audio_buffer = []
        if input_iu.dispatch:
            # Loop over all frames (frame-sized chunks of data) in the input IU
            # and add them to the buffer to be dispatched by the
            # _dispatch_audio_loop
            for i in range(0, input_iu.nframes, self.target_chunk_size):
                cur_pos = i * self.sample_width
                data = input_iu.raw_audio[cur_pos : cur_pos + cur_width]
                distance = cur_width - len(data)
                data += b"\0" * distance

                completion = float((i + self.target_chunk_size) / input_iu.nframes)
                if completion > 1:
                    completion = 1

                current_iu = self.create_iu(input_iu)
                current_iu.set_dispatching(completion, True)
                current_iu.set_audio(
                    data, self.target_chunk_size, self.rate, self.sample_width
                )
                self.audio_buffer.append(current_iu)
            self.set_dispatching(True)
        return None

    def _dispatch_audio_loop(self):
        """A method run in a thread that adds IU to the output queue."""
        while self.run_loop:
            with self.dispatching_mutex:
                if self._is_dispatching:
                    if self.audio_buffer:
                        self.append(self.audio_buffer.pop(0))
                    else:
                        self._is_dispatching = False
                if not self._is_dispatching:  # no else here! bc line above
                    if self.continuous:
                        current_iu = self.create_iu(None)
                        current_iu.set_audio(
                            self.silence,
                            self.target_chunk_size,
                            self.rate,
                            self.sample_width,
                        )
                        current_iu.set_dispatching(0.0, False)
                        self.append(current_iu)
            time.sleep((self.target_chunk_size / self.rate) / self.speed)

    def prepare_run(self):
        self.run_loop = True
        t = threading.Thread(target=self._dispatch_audio_loop)
        t.start()

    def shutdown(self):
        self.run_loop = False
        self.audio_buffer = []


class AudioRecorderModule(abstract.AbstractConsumingModule):
    """A Module that consumes AudioIUs and saves them as a PCM wave file to
    disk."""

    @staticmethod
    def name():
        return "Audio Recorder Module"

    @staticmethod
    def description():
        return "A Module that saves incoming audio to disk."

    @staticmethod
    def input_ius():
        return [AudioIU]

    def __init__(self, filename, rate=44100, sample_width=2, **kwargs):
        """Initialize the audio recorder module.

        Args:
            filename (string): The file name where the audio should be recorded
                to. The path to the file has to be created beforehand.
            rate (int): The sample rate of the input and thus of the wave file.
                Defaults to 44100.
            sample_width (int): The width of one sample. Defaults to 2.
        """
        super().__init__(**kwargs)
        self.filename = filename
        self.wavfile = None
        self.rate = rate
        self.sample_width = sample_width

    def process_iu(self, input_iu):
        self.wavfile.writeframes(input_iu.raw_audio)

    def setup(self):
        self.wavfile = wave.open(self.filename, "wb")
        self.wavfile.setframerate(self.rate)
        self.wavfile.setnchannels(CHANNELS)
        self.wavfile.setsampwidth(self.sample_width)

    def shutdown(self):
        self.wavfile.close()
