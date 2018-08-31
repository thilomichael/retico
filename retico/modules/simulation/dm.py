"""A Module for the dialogue management in the conversation simulation."""

import time
import threading
import random
import math

from retico.core import abstract
from retico.core.dialogue.common import DialogueActIU, DispatchableActIU
from retico.core.audio.common import DispatchedAudioIU
from retico.core.prosody.common import EndOfTurnIU
from retico.dialogue.manager.agenda import AgendaDialogueManager
from retico.dialogue.manager.ngram import NGramDialogueManager


class SimulatedDialogueManagerModule(abstract.AbstractModule):
    """A Simulated Dialogue Manager"""

    EVENT_DIALOGUE_END = "dialogue_end"
    EVENT_SAID = "said"
    EVENT_HEARD = "heard"

    @staticmethod
    def name():
        return "Simulated DM Module"

    @staticmethod
    def description():
        return "A dialogue manager for a simulated conversation"

    @staticmethod
    def input_ius():
        return [DialogueActIU, DispatchedAudioIU, EndOfTurnIU]

    @staticmethod
    def output_iu():
        return DispatchableActIU

    def __init__(self, first_utterance,
                 **kwargs):
        super().__init__(**kwargs)

        self.dialogue_manager = None
        self.is_dispatching = False
        self.dispatching_completion = 0.0
        self.last_utterance = 0.0
        self.last_utterance_begin = 0.0
        self.interlocutor_talking = False
        self.eot_prediction = 0.0
        self.last_interl_utterance = 0.0
        self.last_interl_utterance_begin = 0.0
        self.current_incoming_da = None
        self.dialogue_finished = False
        self.first_utterance = first_utterance
        if first_utterance:
            self.role = "Callee"
        else:
            self.role = "Caller"
        self.fu = True
        self.rnd = random.random()
        self.received_goodbye = False
        self.said_goodbye = False

    def speak(self):
        act, concepts = self.dialogue_manager.next_act()
        if time.time() - self.last_interl_utterance > 20 and act != "greeting":
            act = "greeting"
            concepts = {}
        if concepts.keys():
            fd = "%s:%s" % (act, ",".join(concepts.keys()))
        else:
            fd = act
        output_iu = self.create_iu(None)
        output_iu.set_act(act, concepts)
        output_iu.meta_data["message_data"] = fd
        output_iu.dispatch = True
        self.append(output_iu)
        if act == "goodbye":
            self.said_goodbye = True
        self.event_call(self.EVENT_SAID, data={"iu": output_iu})
        self.is_dispatching = True
        self.last_utterance_begin = time.time()
        self.rnd = random.random()

    def time_until_eot(self):
        right_now = time.time()
        if self.interlocutor_talking:
            blah = right_now - self.last_interl_utterance_begin
            eotp = self.eot_prediction
            if eotp == 0:
                eotp = 0.000001
            x = blah * (1 / eotp)
            x -= blah
            return -x
        else:
            return right_now - self.last_interl_utterance

    def gando_model(self, x):
        if x == 0:
            x = 0.0000001
        out = -0.322581 * math.log(0.433008 * (-1 + 1/x))
        if out > 1:
            out *= 0.5
        return out

    def pause_model(self, x):
        if x == 0:
            x = 0.0000001
        result = -0.196366 * math.log(0.0767043 * (-1 + 1/x))
        while result < 0:
            result = -0.196366 * math.log(0.0767043 * (-1 + 1/random.random()))
        return result + ((time.time()-self.last_interl_utterance)/10)

    def continous_loop(self):
        while not self.dialogue_finished:
            right_now = time.time()
            ts_last_utterance = right_now - self.last_utterance
            ts_last_interl_utterance = right_now - self.last_interl_utterance
            is_silence = not self.is_dispatching and not self.interlocutor_talking
            i_spoke_last = ts_last_utterance < ts_last_interl_utterance

            # if self.agent_class == "callee":
            #     print(self.time_until_eot())
            #     print("ts_last_utterance", ts_last_utterance)
            #     print("ts_last_interl_utterance", ts_last_interl_utterance)
            #     print("me talking", self.is_dispatching)
            #     print("he talking", self.interlocutor_talking)
            #     print("disp completion", self.dispatching_completion)
            #     print("eot  completion", self.eot_prediction)
            #     print("")
            #     print("is silence", is_silence)
            #     print("i spoke last", i_spoke_last)
            #     print("rnd", self.gando_model(self.rnd))
            #     print("t until eot", self.time_until_eot())
            #     print("")
            #     print("")

            if self.fu:
                if self.first_utterance:
                    self.speak()
                    self.fu = False
                    self.last_interl_utterance = time.time()
            else:
                if is_silence:
                    if i_spoke_last:
                        if ts_last_utterance > self.pause_model(self.rnd):
                            self.speak()
                    else:
                        if self.gando_model(self.rnd) <= self.time_until_eot():
                            iu = self.current_incoming_da
                            self.dialogue_manager.process_act(iu.act, iu.concepts)
                            self.speak()
                else:
                    if self.is_dispatching and self.interlocutor_talking:
                        if (self.dispatching_completion > 0.2 and self.dispatching_completion < 0.8) or (self.eot_prediction > 0.2 and self.eot_prediction < 0.8):
                            if random.random() < 0.05:
                                print("SILENCING", self.role)
                                output_iu = self.create_iu(None)
                                output_iu.set_act("", {})
                                output_iu.dispatch = False
                                self.append(output_iu)
                                self.rnd = random.random() + 0.2
                                if self.rnd > 1:
                                    self.rnd = 0.99
                    elif not self.is_dispatching:
                        if self.gando_model(self.rnd) <= self.time_until_eot():
                            if right_now - self.last_interl_utterance_begin < 1.5:
                                continue
                            iu = self.current_incoming_da
                            if not iu:
                                continue
                            self.event_call(self.EVENT_HEARD, data={"iu": iu})
                            self.dialogue_manager.process_act(iu.act, iu.concepts)
                            self.speak()
                        if self.time_until_eot() < 0.001 and self.current_incoming_da and self.current_incoming_da.act == "goodbye":
                            self.received_goodbye = True
                            if self.said_goodbye:
                                self.event_call(self.EVENT_DIALOGUE_END)
            time.sleep(0.05)

    def process_iu(self, input_iu):
        # First, we switch between the different types of IUs
        if isinstance(input_iu, DialogueActIU):
            # print(self.agent_class, "received DialogueAct", input_iu.act)
            if self.fu:
                self.last_interl_utterance = time.time()
                self.last_utterance = time.time()
            self.fu = False
            self.current_incoming_da = input_iu
        elif isinstance(input_iu, DispatchedAudioIU):
            # Track our own dispatching status
            # print(self.agent_class, input_iu.is_dispatching)
            if self.is_dispatching and not input_iu.is_dispatching:
                self.last_utterance = time.time()
            self.is_dispatching = input_iu.is_dispatching
            self.dispatching_completion = input_iu.completion
        elif isinstance(input_iu, EndOfTurnIU):
            if self.interlocutor_talking and not input_iu.is_speaking:
                self.last_interl_utterance = time.time()
            elif input_iu.is_speaking and not self.interlocutor_talking:
                self.last_interl_utterance_begin = time.time()
            self.interlocutor_talking = input_iu.is_speaking
            self.eot_prediction = input_iu.probability
            if self.eot_prediction > 0.99:
                self.dialogue_manager.process_act(self.current_incoming_da.act,
                                                  self.current_incoming_da.concepts)
                self.rnd = random.random()
        return None

    def setup(self):
        self.dialogue_finished = False

    def prepare_run(self):
        t = threading.Thread(target=self.continous_loop)
        t.start()

    def shutdown(self):
        self.dialogue_finished = True

    def __repr__(self):
        return super().__repr__() + " " + self.role


class AgendaDialogueManagerModule(SimulatedDialogueManagerModule):
    "An agenda-based dialogue manager"

    @staticmethod
    def name():
        return "Agenda DM Module"

    def __init__(self, agenda_file, aa_file, first_utterance, **kwargs):
        super().__init__(first_utterance, **kwargs)
        self.agenda_file = agenda_file
        self.aa_file = aa_file
        self.first_utterance = first_utterance
        self.dialogue_manager = AgendaDialogueManager(aa_file, agenda_file,
                                                      first_utterance)


class NGramDialogueManagerModule(SimulatedDialogueManagerModule):
    "An n-gram dialogue manager module"

    @staticmethod
    def name():
        return "N-Gram DM Module"

    def __init__(self, ngram_model, first_utterance, **kwargs):
        super().__init__(first_utterance, **kwargs)
        self.ngram_model = ngram_model
        self.first_utterance = first_utterance
        if first_utterance:
            self.dialogue_manager = NGramDialogueManager(ngram_model, "callee")
        else:
            self.dialogue_manager = NGramDialogueManager(ngram_model, "caller")
