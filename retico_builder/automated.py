import time
import os
import shutil
import argparse

from retico.headless import load
from retico.core.audio.io import SpeakerModule, StreamingSpeakerModule

class AutomatedExecution():

    def __init__(self, file, num_runs=10, audio_output=False,
                 end_sim_event="dialogue_end", output_folder="sims/auto_sims",
                 log_files=["recording_caller.wav", "recording_callee.wav", "transcript.txt", "acts.txt"]):
        self.file = file
        self.num_runs = num_runs
        self.audio_output = audio_output
        self.end_sim_event = end_sim_event
        self.output_folder = output_folder
        self.log_files = log_files

        self.is_running = False

    def end_sim(self, module, event_name, data):
        print("SIMULATION ENDS HERE")
        self.is_running = False

    def run_sims(self):
        if not os.path.exists(self.output_folder):
            os.mkdir(self.output_folder)
        print("Running %d simulations..." % self.num_runs)
        for i in range(self.num_runs):
            print("Running simulation %d" % i)
            modules, _ = load(self.file)

            new_modules = []
            for module in modules:
                if isinstance(module, (SpeakerModule, StreamingSpeakerModule)) \
                 and not self.audio_output:
                    print("Removed speaker %s" % module)
                    module.remove()
                    continue
                module.event_subscribe(self.end_sim_event, self.end_sim)
                module.setup()
                new_modules.append(module)
            modules = new_modules

            self.is_running = True
            for module in modules:
                module.run(run_setup=False)
            while self.is_running:
                time.sleep(0.01)
            time.sleep(2)
            for module in modules:
                module.stop()
            time.sleep(2)
            print("Simulation %d finished" % i)
            current_path = os.path.join(self.output_folder, "iteration%d" % i)
            print("Saving into folder: %s" % current_path)
            os.mkdir(current_path)
            for log_file in self.log_files:
                shutil.move(log_file, current_path)

def parse_arguments():
    p = argparse.ArgumentParser(description='Automatically executes a '
                                            'network until a specific event'
                                            ' occurs.')
    p.add_argument('file', type=str,
                   help='The file that should be loaded')
    p.add_argument('-n', '--num-runs', type=int, default=10,
                   help='Number of times the network should be executed')
    p.add_argument('-a', '--activate-audio', action="store_const",
                   dest="audio_output", default=False, const=True,
                   help='A switch if the network should enable audio output')
    p.add_argument('-e', '--event', type=str, default="dialogue_end",
                   help='The event that should trigger the end of the \
                         simulation')
    p.add_argument('-o', '--output-folder', type=str, default="sims/auto_sims",
                   help='The folder where the log files should be saved')
    p.add_argument('-f', '--files', type=str,
                   default='recording_caller.wav, recording_callee.wav, \
                            transcript.txt, acts.txt',
                   help='The log files that should be saved in the output \
                         folder')
    return p.parse_args()


if __name__ == '__main__':
    arguments = parse_arguments()
    log_files = [a.strip() for a in arguments.files.split(",")]
    ae = AutomatedExecution(arguments.file,
                            num_runs=arguments.num_runs,
                            audio_output=arguments.audio_output,
                            end_sim_event=arguments.event,
                            output_folder=arguments.output_folder,
                            log_files=log_files)
    ae.run_sims()
