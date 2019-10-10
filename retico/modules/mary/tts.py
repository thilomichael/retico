import http.client
import os
import subprocess
import wave
import urllib
import random
from hashlib import blake2b

from retico.core import abstract, text, audio


class MaryTTS:
    """
    A mary TTS class that is able to return the audio as pcm.

    This class relies on a mary tts server rinning and ffmpeg to be installed
    and available.
    """

    CACHING_DIR = "data/mtts_cache/"
    TEMP_DIR = "/tmp"
    TEMP_NAME = "tmp_tts_%s" % random.randint(1000, 10000)

    def __init__(
        self,
        language_code="de",
        voice_name="bits1-hsmm",
        server_address="127.0.0.1",
        server_port=59125,
        caching=True,
    ):
        """
        Creates a Mart TTS instance with the specified language_code and voice_name.
        The valid values can be looked up [here](http://mary.dfki.de/documentation/index.html).

        Args:
            language_code (str): The language code specified by mary tts (e.g. de or en_US)
            voice_name (str): The name of the voice specified by mary tts
            server_address (str): The ip address of the mary tts server
            server_port (str): The port on which the mary tts server is running
            caching (bool): Whether the tts should cache the speech.
        """
        self.language_code = language_code
        self.voice_name = voice_name
        self.server_address = server_address
        self.server_port = server_port
        self.caching = caching

        self.wav_sample_rate = 44100  # 44100 sample rate / See ffmpeg
        self.wav_codec = "pcm_s16le"  # 16-bit little endian codec / See ffmpeg

        # Create caching directory if it not already exists
        if not os.path.exists(self.CACHING_DIR):
            os.mkdir(self.CACHING_DIR)

    def get_cache_path(self, text):
        """
        Creates a hash of the given TTS settings and returns a unique path to the cached version of the synthesis.
        This method does not check for the cached file to exist!

        Args:
            text (str): The text to synthesis (this is included in the hash that is used for the cache path)

        Returns (str): Path to a cached version of that synthesis.

        """
        h = blake2b(digest_size=16)
        h.update(bytes(text, "utf-8"))
        h.update(bytes(self.voice_name, "utf-8"))
        h.update(bytes(self.language_code, "utf-8"))
        h.update(bytes(self.wav_codec, "utf-8"))
        h.update(bytes(str(self.wav_sample_rate), "utf-8"))  # Does this make sense?
        text_digest = h.hexdigest()

        return os.path.join(self.CACHING_DIR, text_digest)

    def tts(self, text):
        """
        Synthesizes the text given and returns it in PCM format. This method uses the wave_sample_rate and wave_codec
        properties to determine the shape of the synthesized audio.
        The returned audio does not have any wave header but contains jus the pure PCM data.

        Args:
            text (str): The text to synthesize

        Returns (bytes): The synthesized text in raw PCM format.
        """
        cache_path = self.get_cache_path(text)
        if os.path.isfile(cache_path):
            wav_audio = None
            with open(cache_path, "rb") as cfile:
                wav_audio = cfile.read()
        else:
            mtts_audio = self.mary_tts_call(text)
            wav_audio = self.convert_audio(mtts_audio)
            with open(cache_path, "wb") as cfile:
                cfile.write(wav_audio)

        return wav_audio

    def mary_tts_call(self, text):
        """
        This method does a Mary TTS call and returns the response (audio data in WAVE format) as bytes
        Args:
            text (str): The string to be synthesized

        Returns (bytes): Audio data in WAVE format as bytes.

        """
        h1 = http.client.HTTPConnection(f"{self.server_address}:{self.server_port}")
        text = urllib.parse.quote_plus(text)
        request_str = (
            "/process?INPUT_TEXT=%s&INPUT_TYPE=TEXT&OUTPUT_TYPE=AUDIO&AUDIO=WAVE_FILE&LOCALE=%s&VOICE=%s"
            % (text, self.language_code, self.voice_name)
        )
        h1.request("GET", request_str)

        r1 = h1.getresponse()
        response = r1.read()
        return response

    def convert_audio(self, audio):
        """
        Converts the given wav audio to the respecitve pcm data through ffmpeg.
        This function assumes ffmpeg is installed and readily available.

        Args:
            audio (bytes): The wav audio data as given by Mary TTS

        Returns (bytes): The pcm data as specified by wav_codec and wav_sample_rate. Note that this byte array does not
            contain the wave header (or any other header) but is just the raw audio data.

        """
        tmp_mary_name = self.TEMP_NAME + "_mtts.wav"
        tmp_wav_name = self.TEMP_NAME + ".wav"
        tmp_mary_path = os.path.join(self.TEMP_DIR, tmp_mary_name)
        tmp_wav_path = os.path.join(self.TEMP_DIR, tmp_wav_name)

        with open(tmp_mary_path, "wb") as f:
            f.write(audio)

        subprocess.call(
            [
                "ffmpeg",
                "-i",
                tmp_mary_path,
                "-acodec",
                self.wav_codec,
                "-ar",
                str(self.wav_sample_rate),
                tmp_wav_path,
                "-y",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        wav_audio = None
        with wave.open(tmp_wav_path, "rb") as wav_file:
            w_length = wav_file.getnframes()
            wav_audio = wav_file.readframes(w_length)

        # Cleanup
        os.remove(tmp_mary_path)
        os.remove(tmp_wav_path)

        return wav_audio


class MaryTTSModule(abstract.AbstractModule):
    """A Mary TTS Module that uses Marry TTS to synthesize audio."""

    @staticmethod
    def name():
        return "Mary TTS Module"

    @staticmethod
    def description():
        return "A module that uses Mary TTS to synthesize audio."

    @staticmethod
    def input_ius():
        return [text.common.GeneratedTextIU]

    @staticmethod
    def output_iu():
        return audio.common.SpeechIU

    def __init__(
        self,
        language_code,
        voice_name,
        server_address="localhost",
        server_port=59125,
        caching=True,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.language_code = language_code
        self.voice_name = voice_name
        self.server_address = server_address
        self.server_port = server_port
        self.caching = caching
        self.mtts = MaryTTS(
            language_code, voice_name, server_address, server_port, caching
        )
        self.sample_width = 2
        self.rate = 44100

    def process_iu(self, input_iu):
        output_iu = self.create_iu(input_iu)
        raw_audio = self.mtts.tts(input_iu.get_text())
        nframes = len(raw_audio) / self.sample_width
        output_iu.set_audio(raw_audio, nframes, self.rate, self.sample_width)
        output_iu.dispatch = input_iu.dispatch
        return output_iu
