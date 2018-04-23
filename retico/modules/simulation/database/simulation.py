"""
A module providing data for the simulation modules.

The database contains the following information:
    - raw audio: The audio that corresponds to the text that is queried
    - dialogue act: The dialogue act
    - concepts: The concepts contained in the act
    - transcription: The transcription of the act
    - source: The original source of the utterance
"""

import glob
from os import path
import csv
import wave


class SimulationData():
    """A data object containing information about the loaded data.

    Attributes:
        tbd...
    """

    def generate_meta(self):
        """Generate a dict with all the information.

        This can be used as meta data for an Incremental Unit.

        Returns:
            dict: A dictionary containing all the fields of an SimulationData
            object
        """
        meta = {}
        meta["dialogue_act"] = self.dialogue_act
        meta["concepts"] = self.concepts

        meta["raw_audio"] = self.raw_audio
        meta["frame_rate"] = self.frame_rate
        meta["sample_width"] = self.sample_width

        meta["transcription"] = self.transcription
        meta["confidence"] = self.confidence

        meta["audio_file_path"] = self.audio_file_path
        meta["csv_file_path"] = self.csv_file_path

        meta["csv_row"] = self.csv_row

        return meta

    def __init__(self, audio_file_path, csv_file_path, row):
        self.dialogue_act = None
        self.concepts = None

        self.raw_audio = None
        self.frame_rate = 0
        self.sample_width = 0

        self.transcription = None
        self.confidence = 0

        self.audio_file_path = audio_file_path
        self.csv_file_path = csv_file_path

        self.csv_row = row

    def set_dialogue_act(self, act_concept):
        """Set the dialogue act givena a string found in the csv file.

        The string contains the act and optionally a list of concepts. The act
        and the concepts are separated by a colon (:) and the concepts itself
        are separated by comma (,).

        Args:
            act_concept (str): A combined string of act and concept
        """
        splt = act_concept.split(":")
        self.dialogue_act = splt[0]
        self.concepts = {}
        if len(splt) > 1:
            for concept in splt[1].split(","):
                self.concepts[concept] = "???"

    def set_audio(self, raw_audio, frame_rate, sample_width):
        """Set the audio given the raw audio, frame rate and sample width.

        Args:
            raw_audio (bytes): An array of bytes containing the raw audio.
            frame_rate: The frame rate of the audio blob.
            sample_width: The width of one sample in bytes.
        """
        self.raw_audio = raw_audio
        self.frame_rate = frame_rate
        self.sample_width = sample_width

    def set_transcription(self, transcription, confidence):
        """Set the transcription and the confidence.

        Args:
            transcription (str): The transcription of the utterance.
            confidence (float): The confidence of that transcription.
        """
        self.transcription = transcription
        self.confidence = confidence


class SimulatioDB():
    """A database for the Simulation modules."""

    @staticmethod
    def get_wave_data(wav_file, startpos, endpos):
        """Return the wave data inside a wave_file given the start position and
        end position is milliseconds.

        Args:
            wav_file (wave.Wave_read): A wave file
            startpos (int): The starting position of the utterace to be
                extracted in milliseconds.
            endpos (int): The ending position of the utterance to be extracted
                in milliseconds.

        Returns:
            bytes: A bytes array containing the utterance between startpos and
            endpos.
        """
        wav_file.setpos(int((startpos / 1000) * wav_file.getframerate()))
        duration = endpos - startpos
        return wav_file.readframes(int(wav_file.getframerate() *
                                       (duration / 1000)))

    @staticmethod
    def csv_wav_pair(data_directory):
        """Opens the csv and wav files contained in the given path and yields
        them."""
        glob_path = path.join(data_directory, "*.txt")
        for csv_p in glob.glob(glob_path):
            wav_p = csv_p.replace(".txt", ".wav")
            with open(csv_p, 'r') as csv_f, wave.open(wav_p, 'rb') as wav_f:
                reader = csv.reader(csv_f, delimiter="\t")
                yield reader, wav_f, csv_p, wav_p

    def read_data(self, data_directory):
        """Reads the data from file into a data structure."""
        for csv_f, wav_f, csv_p, wav_p in self.csv_wav_pair(data_directory):
            current_rate = wav_f.getframerate()
            current_sample_width = wav_f.getsampwidth()
            for row in csv_f:
                if len(row) != 7:
                    continue
                if row[1] != self.agent_type:
                    continue
                data = SimulationData(wav_p, csv_p, row)
                data.set_transcription(row[5], float(row[6]))
                data.set_dialogue_act(row[4])
                wav_data = self.get_wave_data(wav_f, int(row[2]), int(row[3]))
                data.set_audio(wav_data, current_rate, current_sample_width)
                yield data

    def __init__(self, data_directory, agent_type):
        self.data_directory = data_directory
        self.agent_type = agent_type
        self.act_db = {}

        for idata in self.read_data(data_directory):
            if not self.act_db.get(idata.dialogue_act):
                self.act_db[idata.dialogue_act] = []
            self.act_db[idata.dialogue_act].append(idata)

    def query(self, dialogue_act, concepts):
        """Queries the database and returns a list of candiates having the same
        dialogue act and the same concepts.

        While the type of concepts will be all the same, their actual values
        may differ.

        Args:
            dialogue_act (str): A string representation of a dialogue act. All
                lower case.
            concepts (dict): A dictionary mapping names of concepts to their
                values.

        Returns:
            SimulationData: Data structures that have the same dialogue_act and
            the same concept types as given in the arguments.
        """
        candidates = []
        if not self.act_db.get(dialogue_act):
            return []
        for idata in self.act_db[dialogue_act]:
            if set(concepts.keys()) == set(idata.concepts.keys()):
                candidates.append(idata)
        return candidates


if __name__ == '__main__':
    idb = SimulatioDB("data/sct11", "caller")
    for candidate in idb.query("provide_info", {"caller_name": "Jeremy Clems"}):
        print(candidate.generate_meta())
