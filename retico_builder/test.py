import sys
from retico.core.audio.io import MicrophoneModule, SpeakerModule, AudioDispatcherModule, StreamingSpeakerModule, AudioRecorderModule
from retico.core.debug.general import CallbackModule
from retico.core.text.asr import TextDispatcherModule

from retico.modules.google.asr import GoogleASRModule
from retico.modules.google.tts import GoogleTTSModule
from retico.modules.mary.tts import MaryTTSModule
from retico.modules.rasa.nlu import RasaNLUModule

from retico.modules.simulation.dm import ConvSimDialogueManagerModule
from retico.modules.simulation.dm import AgendaDialogueManagerModule
from retico.modules.simulation.dm import NGramDialogueManagerModule
from retico.modules.simulation.dm import RasaDialogueManagerModule
from retico.modules.simulation.nlg import SimulatedNLGModule
from retico.modules.simulation.tts import SimulatedTTSModule
from retico.modules.simulation.asr import SimulatedASRModule
from retico.modules.simulation.nlu import SimulatedNLUModule
from retico.modules.simulation.eot import SimulatedEoTModule

from retico.modules.net.network import DelayedNetworkModule

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
    m2 = GoogleASRModule("en-US") # en-US or de-DE or ....
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

def repeat_demo():
    m1 = MicrophoneModule(5000)
    m2 = GoogleASRModule("en-US")
    m3 = TextDispatcherModule()
    m4 = GoogleTTSModule("en-US", "en-US-Wavenet-A")
    m5 = AudioDispatcherModule(5000)
    m6 = StreamingSpeakerModule(5000)

    m1.subscribe(m2)
    m2.subscribe(m3)
    m3.subscribe(m4)
    m4.subscribe(m5)
    m5.subscribe(m6)

    m1.setup()
    m2.setup()
    m3.setup()
    m4.setup()
    m5.setup()
    m6.setup()

    print("All setup")

    m1.run(run_setup=False)
    m2.run(run_setup=False)
    m3.run(run_setup=False)
    m4.run(run_setup=False)
    m5.run(run_setup=False)
    m6.run(run_setup=False)

    input()

    m1.stop()
    m2.stop()
    m3.stop()
    m4.stop()
    m5.stop()
    m6.stop()

def rasa_nlu():
    m1 = MicrophoneModule(5000)
    m2 = GoogleASRModule("en-US")
    m3 = CallbackModule(callback=lambda x: print("%s (%f) - %s" % (x.text, x.confidence, x.final)))
    m4 = RasaNLUModule("data/rasa/models/nlu/default/current")
    m5 = CallbackModule(callback=lambda x: print(x.act, "-", x.concepts))

    m1.subscribe(m2)
    m2.subscribe(m3)
    m2.subscribe(m4)
    m4.subscribe(m5)

    m4.setup()
    m2.setup()
    m1.setup()
    m3.setup()
    m5.setup()

    print("All setup")

    m1.run(run_setup=False)
    m2.run(run_setup=False)
    m3.run(run_setup=False)
    m4.run(run_setup=False)
    m5.run(run_setup=False)

    input()

    m1.stop()
    m2.stop()
    m3.stop()
    m4.stop()
    m5.stop()

def simulation_mary(caller_dm, callee_dm, convtype, delay):
    caller_tts = MaryTTSModule("de", "bits1-hsmm")
    callee_tts = MaryTTSModule("de", "bits3-hsmm")
    simulation(caller_tts, callee_tts, caller_dm, callee_dm, convtype, delay)

def simulation_google(caller_dm, callee_dm, convtype, delay):
    caller_tts = GoogleTTSModule("de-DE", "de-DE-Wavenet-A")
    callee_tts = GoogleTTSModule("de-DE", "de-DE-Wavenet-B")
    simulation(caller_tts, callee_tts, caller_dm, callee_dm, convtype, delay)

def simulation_simasr(caller_dm, callee_dm, convtype, delay):
    caller_tts = SimulatedTTSModule()
    callee_tts = SimulatedTTSModule()
    simulation(caller_tts, callee_tts, caller_dm, callee_dm, convtype, delay)

def simulation(caller_tts, callee_tts, caller_dm, callee_dm, convtype, delay):
    caller_nlg = SimulatedNLGModule("data/%s/audio" % convtype, agent_type="caller")
    caller_io  = AudioDispatcherModule(5000)
    caller_asr = SimulatedASRModule()
    caller_nlu = SimulatedNLUModule()
    caller_eot = SimulatedEoTModule()
    caller_speaker = SpeakerModule(use_speaker="left")
    caller_recorder = AudioRecorderModule("recording_caller.wav")

    callee_nlg = SimulatedNLGModule("data/%s/audio" % convtype, agent_type="callee")
    callee_io  = AudioDispatcherModule(5000)
    callee_asr = SimulatedASRModule()
    callee_nlu = SimulatedNLUModule()
    callee_eot = SimulatedEoTModule()
    callee_speaker = SpeakerModule(use_speaker="right")
    callee_recorder = AudioRecorderModule("recording_callee.wav")

    network = DelayedNetworkModule(delay)

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

    headless.save(caller_dm, "simulation_%s" % convtype)

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

def _get_sim_func(simtype):
    if simtype == "gtts":
        return simulation_google
    elif simtype == "mtts":
        return simulation_mary
    else:
        return simulation_simasr

def convsim_simulation(convtype, simtype, delay):
    caller_dm = ConvSimDialogueManagerModule("data/%s/callerfile.ini" % convtype, "data/%s/audio" % convtype, "caller", False)
    callee_dm = ConvSimDialogueManagerModule("data/%s/calleefile.ini" % convtype, "data/%s/audio" % convtype, "callee", True)
    simfunc = _get_sim_func(simtype)
    simfunc(caller_dm, callee_dm, convtype, delay)


def agenda_simulation(convtype, simtype, delay):
    caller_dm = AgendaDialogueManagerModule("data/%s/callerfile.ini" % convtype, "data/%s/available_acts_%s_caller.txt" % (convtype, convtype), False)
    callee_dm = AgendaDialogueManagerModule("data/%s/calleefile.ini" % convtype, "data/%s/available_acts_%s_callee.txt" % (convtype, convtype), True)
    simfunc = _get_sim_func(simtype)
    simfunc(caller_dm, callee_dm, convtype, delay)

def ngram_simulation(convtype, simtype, delay):
    caller_dm = NGramDialogueManagerModule("data/%s/ngram_dm/combined-model.pickle" % convtype, False)
    callee_dm = NGramDialogueManagerModule("data/%s/ngram_dm/combined-model.pickle" % convtype, True)
    simfunc = _get_sim_func(simtype)
    simfunc(caller_dm, callee_dm, convtype, delay)

def rasa_simulation(convtype, simtype, delay):
    caller_dm = RasaDialogueManagerModule("data/%s/rasa_models/caller/" % convtype, False)
    callee_dm = RasaDialogueManagerModule("data/%s/rasa_models/callee/" % convtype, True)
    simfunc = _get_sim_func(simtype)
    simfunc(caller_dm, callee_dm, convtype, delay)


if __name__ == '__main__':
    simtype = ""
    if len(sys.argv) > 3:
        simtype = sys.argv[3]
    delay = 0.0
    if len(sys.argv) > 4:
        delay = float(sys.argv[4])
    if sys.argv[1] == "audio":
        audio_demo()
    elif sys.argv[1] == "google":
        google_asr()
    elif sys.argv[1] == "rasa_nlu":
        rasa_nlu()
    elif sys.argv[1] == "convsim":
        convsim_simulation(sys.argv[2], simtype, delay)
    elif sys.argv[1] == "agenda":
        agenda_simulation(sys.argv[2], simtype, delay)
    elif sys.argv[1] == "ngram":
        ngram_simulation(sys.argv[2], simtype, delay)
    elif sys.argv[1] == "rasa":
        rasa_simulation(sys.argv[2], simtype, delay)
    elif sys.argv[1] == "repeat":
        repeat_demo()
