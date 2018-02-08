"""
A Module mainly for adding the turn relevant places to the audio dispatching.
"""

from retico.audio.io import AudioDispatcherModule


class SimulatedDispatcherModule(AudioDispatcherModule):
    """A module that adds turn relevant information to the dispatched audio."""
    @staticmethod
    def name():
        return "Simulated Audio Dispatching Module"

    @staticmethod
    def description():
        return ("A module that transmits audio by splitting it up into"
                "streamable pakets and adds turn taking information.")

    def process_iu(self, input_iu):
        cur_width = self.target_chunk_size * self.sample_width
        self.set_dispatching(False)
        self.audio_buffer = []
        if input_iu.dispatch:
            # If dispatch, then cut the audio into chunks of [target_chunk_size]
            for i in range(0, input_iu.nframes, self.target_chunk_size):
                cur_pos = i * self.sample_width
                data = input_iu.raw_audio[cur_pos:cur_pos + cur_width]
                distance = cur_width - len(data)

                # Add silence if the last audio chunk is not large enough.
                data += b'\0' * distance

                # Calculate the completion rate and make sure it always reaches
                # 1 in the end.
                completion = float((i + self.target_chunk_size)
                                   / input_iu.nframes)
                if completion > 1:
                    completion = 1

                current_iu = self.create_iu(input_iu)
                current_iu.meta_data["completion"] = completion
                current_iu.set_audio(data, self.target_chunk_size, self.rate,
                                     self.sample_width)
                self.audio_buffer.append(current_iu)
            self.set_dispatching(True)
        return None
