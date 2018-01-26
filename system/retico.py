import time

from incremental import abstract
from incremental.audio.io import MicrophoneModule, SpeakerModule
from incremental.debug.console import DebugModule
from incremental.modules.google.asr import GoogleASRModule

def main():
    print("Hello World! oijoij")
    # input_queue = abstract.IncrementalQueue(None, None)
    m1 = MicrophoneModule(512)
    m2 = SpeakerModule(512)
    m25 = GoogleASRModule()
    m3 = DebugModule()
    m1.subscribe(m25)
    m1.subscribe(m2)
    m25.subscribe(m3)
    m1.run()
    time.sleep(0.1)
    m2.run()
    m25.run()
    m3.run()
    time.sleep(10)
    m1.stop()
    m2.stop()
    m25.stop()
    m3.stop()
    # input_queue.put(abstract.IncrementalUnit(m))
    # m.stop()
    print(abstract.AbstractModule.__subclasses__())

if __name__ == '__main__':
    main()
