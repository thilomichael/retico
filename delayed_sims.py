#!/usr/bin/env python3

import os
import numpy as np
import time
import shutil
import sys

from retico.headless import load
from retico.core.audio.io import SpeakerModule, StreamingSpeakerModule
from retico.modules.net.network import DelayedNetworkModule


OUTPUT_FOLDER = "delayed_sims"
NSIMS = 30
if len(sys.argv) == 2 and (sys.argv[1] == "SCT11" or sys.argv[1] == "RNV1"):
    print(f"Simulatig {sys.argv[1]}")
    CONVTYPE = sys.argv[1]
else:
    CONVTYPE = "SCT11"  # SCT11 or RNV1
sim_base = f"save/simulation_{CONVTYPE.lower()}_delayed800.rtc"
DELAY_LEVELS = np.arange(0, 2.1, 0.1)
is_running = False
log_files = [
    "recording_caller.wav",
    "recording_callee.wav",
    "transcript.txt",
    "acts.txt",
]

if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)


def end_sim(module, event_name, data):
    print("SIMULATION ENDS HERE")
    global is_running
    is_running = False


def do_sim(delay_level, i):
    global sim_base, is_running, log_files
    print(f"  Simulation {i}")
    modules, _ = load(sim_base)
    new_modules = []
    for module in modules:
        if isinstance(module, (SpeakerModule, StreamingSpeakerModule)):
            module.remove()
            continue
        if isinstance(module, DelayedNetworkModule):
            module.delay = delay_level
        module.event_subscribe("dialogue_end", end_sim)
        module.event_subscribe(
            "doubletalk", lambda a, b, c: print(f"Double Talk {a.tt_delay}")
        )
        module.setup()
        new_modules.append(module)
    modules = new_modules

    is_running = True
    for module in modules:
        module.run(run_setup=False)
    counter = 0
    while is_running:
        time.sleep(0.01)
        counter += 1
        if counter > 30000:  # 5 * 60 * 100
            print("\n\nSIM FAILED!? ABORT AND RETRY!!\n\n")
            for module in modules:
                module.stop()
            time.sleep(10)
            do_sim(delay_level, i)  # retry
            return

    time.sleep(2)
    for module in modules:
        module.stop()
    time.sleep(4)

    current_path = os.path.join(current_folder, "iteration%d" % i)
    os.mkdir(current_path)
    for log_file in log_files:
        shutil.move(log_file, current_path)


for delay_level in DELAY_LEVELS:
    current_folder = f"{OUTPUT_FOLDER}/{CONVTYPE}_{int(delay_level*1000)}"
    if not os.path.exists(current_folder):
        os.makedirs(current_folder)
    print(f"Simulating {NSIMS} {CONVTYPE} coversations with {delay_level:.1f} s delay")
    for i in range(NSIMS):
        do_sim(delay_level, i)
