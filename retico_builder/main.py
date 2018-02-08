import time

from retico.modules.simulation import nlg, tts, audio, asr, nlu
from retico.core.audio import io
from retico.core import abstract
from retico.core.dialogue.common import DispatchableActIU
from retico.core.debug.general import CallbackModule


def main():
    print("Hello World! oijoij")
    m1 = nlg.SimulatedNLGModule("data/sct11")
    m2 = tts.SimulatedTTSModule()
    m3 = audio.SimulatedDispatcherModule(5000)
    m4 = io.StreamingSpeakerModule(5000)
    m5 = asr.SimulatedASRModule()
    m6 = nlu.SimulatedNLUModule()
    m7 = CallbackModule(lambda x: print(x.get_text()))
    m8 = io.AudioRecorderModule("test.wav")
    m1.subscribe(m2)
    m2.subscribe(m3)
    m3.subscribe(m4)
    m3.subscribe(m5)
    m5.subscribe(m6)
    m5.subscribe(m7)
    m3.subscribe(m8)
    iQ = abstract.IncrementalQueue(None, m1)
    m1.set_left_buffer(iQ)
    m1.run()
    m2.run()
    m3.run()
    m4.run()
    m5.run()
    m6.run()
    m7.run()
    m8.run()
    input()
    print("MOEP")
    iQ.put(DispatchableActIU(creator=None, act="provide_info", concepts={"reason":"","num_of_persons":"","pizza_type":""}, dispatch=True))
    input()
    print("MOEP")
    iQ.put(DispatchableActIU(creator=None, act="greeting", dispatch=True))
    input()
    print("MOEP")
    iQ.put(DispatchableActIU(creator=None, act="greeting", dispatch=False))
    input()
    m1.stop()
    m2.stop()
    m3.stop()
    m4.stop()
    m5.stop()
    m6.stop()
    m7.stop()
    m8.stop()


if __name__ == '__main__':
    main()
