import sys
from retico.core.audio.io import MicrophoneModule, SpeakerModule, AudioDispatcherModule, StreamingSpeakerModule, AudioRecorderModule
from retico.core.debug.general import CallbackModule

from retico.modules.google.asr import GoogleASRModule
from retico.modules.rasa.nlu import RasaNLUModule

from retico.modules.simulation.dm import ConvSimDialogueManagerModule
from retico.modules.simulation.dm import AgendaDialogueManagerModule
from retico.modules.simulation.nlg import SimulatedNLGModule
from retico.modules.simulation.tts import SimulatedTTSModule
from retico.modules.simulation.asr import SimulatedASRModule
from retico.modules.simulation.nlu import SimulatedNLUModule
from retico.modules.simulation.eot import SimulatedEoTModule

from retico import headless

def audio_demo():
    m1 = MicrophoneModule(5000)
    m2 = StreamingSpeakerModule(5000)

    m1.subscribe(m2)

    m1.run()
    m2.run()

    input()

    m1.stop()
    m2.stop()

    input()

    m1.run()
    m2.run()

    input()

    m1.stop()
    m2.stop()


def google_asr():
    m1 = MicrophoneModule(5000)
    m2 = GoogleASRModule("de-DE") # en-US or de-DE or ....
    m3 = CallbackModule(callback=lambda x: print("%s (%f) - %s" % (x.text, x.stability, x.final)))

    m1.subscribe(m2)
    m2.subscribe(m3)

    m1.run()
    m2.run()
    m3.run()

    input()

    m1.stop()
    m2.stop()
    m3.stop()

def rasa_nlu():
    m1 = MicrophoneModule(5000)
    m2 = GoogleASRModule()
    # m3 = CallbackModule(callback=lambda x: print("%s (%f) - %s" % (x.text, x.confidence, x.final)))
    m4 = RasaNLUModule("data/rasa/models/nlu/current", "data/rasa/nlu_model_config.json")
    m5 = CallbackModule(callback=lambda x: print(x.act, "-", x.concepts))

    m1.subscribe(m2)
    # m2.subscribe(m3)
    m2.subscribe(m4)
    m4.subscribe(m5)

    m4.setup()
    m2.setup()
    m1.setup()
    # m3.setup()
    m5.setup()

    print("All setup")

    m1.run(run_setup=False)
    m2.run(run_setup=False)
    # m3.run(run_setup=False)
    m4.run(run_setup=False)
    m5.run(run_setup=False)

    input()

    m1.stop()
    m2.stop()
    # m3.stop()
    m4.stop()
    m5.stop()

def simulation(thing):
    caller_dm  = ConvSimDialogueManagerModule("data/%s/callerfile.ini" % thing, "data/%s/audio" % thing, "caller", False)
    caller_nlg = SimulatedNLGModule("data/%s/audio" % thing, agent_type="caller")
    caller_tts = SimulatedTTSModule()
    caller_io  = AudioDispatcherModule(5000)
    caller_asr = SimulatedASRModule()
    caller_nlu = SimulatedNLUModule()
    caller_eot = SimulatedEoTModule()
    caller_speaker = SpeakerModule(use_speaker="left")
    caller_recorder = AudioRecorderModule("recording_caller.wav")

    callee_dm  = ConvSimDialogueManagerModule("data/%s/calleefile.ini" % thing, "data/%s/audio" % thing, "callee", True)
    callee_nlg = SimulatedNLGModule("data/%s/audio" % thing, agent_type="callee")
    callee_tts = SimulatedTTSModule()
    callee_io  = AudioDispatcherModule(5000)
    callee_asr = SimulatedASRModule()
    callee_nlu = SimulatedNLUModule()
    callee_eot = SimulatedEoTModule()
    callee_speaker = SpeakerModule(use_speaker="right")
    callee_recorder = AudioRecorderModule("recording_callee.wav")

    caller_dm.subscribe(caller_nlg)
    caller_nlg.subscribe(caller_tts)
    caller_tts.subscribe(caller_io)
    caller_io.subscribe(callee_asr)
    caller_io.subscribe(callee_eot)
    caller_io.subscribe(caller_speaker)
    caller_io.subscribe(caller_recorder)
    caller_io.subscribe(caller_dm)
    callee_asr.subscribe(callee_nlu)
    callee_nlu.subscribe(callee_dm)
    callee_eot.subscribe(callee_dm)
    callee_dm.subscribe(callee_nlg)
    callee_nlg.subscribe(callee_tts)
    callee_tts.subscribe(callee_io)
    callee_io.subscribe(caller_asr)
    callee_io.subscribe(caller_eot)
    callee_io.subscribe(callee_dm)
    callee_io.subscribe(callee_speaker)
    callee_io.subscribe(callee_recorder)
    caller_asr.subscribe(caller_nlu)
    caller_nlu.subscribe(caller_dm)
    caller_eot.subscribe(caller_dm)

    headless.save(caller_dm, "simulation_%s" % thing)

    caller_dm.setup()
    caller_nlg.setup()
    caller_tts.setup()
    caller_io.setup()
    caller_asr.setup()
    caller_nlu.setup()
    caller_eot.setup()
    caller_speaker.setup()
    caller_recorder.setup()
    callee_dm.setup()
    callee_nlg.setup()
    callee_tts.setup()
    callee_io.setup()
    callee_asr.setup()
    callee_nlu.setup()
    callee_eot.setup()
    callee_speaker.setup()
    callee_recorder.setup()

    print("READY")

    caller_dm.run(run_setup=False)
    caller_nlg.run(run_setup=False)
    caller_tts.run(run_setup=False)
    caller_io.run(run_setup=False)
    caller_asr.run(run_setup=False)
    caller_nlu.run(run_setup=False)
    caller_eot.run(run_setup=False)
    caller_speaker.run(run_setup=False)
    caller_recorder.run(run_setup=False)
    callee_dm.run(run_setup=False)
    callee_nlg.run(run_setup=False)
    callee_tts.run(run_setup=False)
    callee_io.run(run_setup=False)
    callee_asr.run(run_setup=False)
    callee_nlu.run(run_setup=False)
    callee_eot.run(run_setup=False)
    callee_speaker.run(run_setup=False)
    callee_recorder.run(run_setup=False)

    input()

    caller_dm.stop()
    caller_nlg.stop()
    caller_tts.stop()
    caller_io.stop()
    caller_asr.stop()
    caller_nlu.stop()
    caller_eot.stop()
    caller_speaker.stop()
    caller_recorder.stop()
    callee_dm.stop()
    callee_nlg.stop()
    callee_tts.stop()
    callee_io.stop()
    callee_asr.stop()
    callee_nlu.stop()
    callee_eot.stop()
    callee_speaker.stop()
    callee_recorder.stop()

def agenda_simulation(thing):
    caller_dm  = AgendaDialogueManagerModule("data/%s/callerfile.ini" % thing, "data/%s/available_acts_%s_caller.txt" % (thing, thing), False)
    caller_nlg = SimulatedNLGModule("data/%s/audio" % thing, agent_type="caller")
    caller_tts = SimulatedTTSModule()
    caller_io  = AudioDispatcherModule(5000)
    caller_asr = SimulatedASRModule()
    caller_nlu = SimulatedNLUModule()
    caller_eot = SimulatedEoTModule()
    caller_speaker = SpeakerModule(use_speaker="left")
    caller_recorder = AudioRecorderModule("recording_caller.wav")

    callee_dm  = AgendaDialogueManagerModule("data/%s/calleefile.ini" % thing, "data/%s/available_acts_%s_callee.txt" % (thing, thing), True)
    callee_nlg = SimulatedNLGModule("data/%s/audio" % thing, agent_type="callee")
    callee_tts = SimulatedTTSModule()
    callee_io  = AudioDispatcherModule(5000)
    callee_asr = SimulatedASRModule()
    callee_nlu = SimulatedNLUModule()
    callee_eot = SimulatedEoTModule()
    callee_speaker = SpeakerModule(use_speaker="right")
    callee_recorder = AudioRecorderModule("recording_callee.wav")

    caller_dm.subscribe(caller_nlg)
    caller_nlg.subscribe(caller_tts)
    caller_tts.subscribe(caller_io)
    caller_io.subscribe(callee_asr)
    caller_io.subscribe(callee_eot)
    caller_io.subscribe(caller_speaker)
    caller_io.subscribe(caller_recorder)
    caller_io.subscribe(caller_dm)
    callee_asr.subscribe(callee_nlu)
    callee_nlu.subscribe(callee_dm)
    callee_eot.subscribe(callee_dm)
    callee_dm.subscribe(callee_nlg)
    callee_nlg.subscribe(callee_tts)
    callee_tts.subscribe(callee_io)
    callee_io.subscribe(caller_asr)
    callee_io.subscribe(caller_eot)
    callee_io.subscribe(callee_dm)
    callee_io.subscribe(callee_speaker)
    callee_io.subscribe(callee_recorder)
    caller_asr.subscribe(caller_nlu)
    caller_nlu.subscribe(caller_dm)
    caller_eot.subscribe(caller_dm)

    headless.save(caller_dm, "simulation_%s" % thing)

    caller_dm.setup()
    caller_nlg.setup()
    caller_tts.setup()
    caller_io.setup()
    caller_asr.setup()
    caller_nlu.setup()
    caller_eot.setup()
    caller_speaker.setup()
    caller_recorder.setup()
    callee_dm.setup()
    callee_nlg.setup()
    callee_tts.setup()
    callee_io.setup()
    callee_asr.setup()
    callee_nlu.setup()
    callee_eot.setup()
    callee_speaker.setup()
    callee_recorder.setup()

    print("READY")

    caller_dm.run(run_setup=False)
    caller_nlg.run(run_setup=False)
    caller_tts.run(run_setup=False)
    caller_io.run(run_setup=False)
    caller_asr.run(run_setup=False)
    caller_nlu.run(run_setup=False)
    caller_eot.run(run_setup=False)
    caller_speaker.run(run_setup=False)
    caller_recorder.run(run_setup=False)
    callee_dm.run(run_setup=False)
    callee_nlg.run(run_setup=False)
    callee_tts.run(run_setup=False)
    callee_io.run(run_setup=False)
    callee_asr.run(run_setup=False)
    callee_nlu.run(run_setup=False)
    callee_eot.run(run_setup=False)
    callee_speaker.run(run_setup=False)
    callee_recorder.run(run_setup=False)

    input()

    caller_dm.stop()
    caller_nlg.stop()
    caller_tts.stop()
    caller_io.stop()
    caller_asr.stop()
    caller_nlu.stop()
    caller_eot.stop()
    caller_speaker.stop()
    caller_recorder.stop()
    callee_dm.stop()
    callee_nlg.stop()
    callee_tts.stop()
    callee_io.stop()
    callee_asr.stop()
    callee_nlu.stop()
    callee_eot.stop()
    callee_speaker.stop()
    callee_recorder.stop()


if __name__ == '__main__':
    if sys.argv[1] == "audio":
        audio_demo()
    elif sys.argv[1] == "google":
        google_asr()
    elif sys.argv[1] == "rasa":
        rasa_nlu()
    elif sys.argv[1] == "simulation":
        simulation(sys.argv[2])
    elif sys.argv[1] == "agenda":
        agenda_simulation(sys.argv[2])
