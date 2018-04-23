"""A Module for the dialogue management in the conversation simulation."""

import time
import threading
import random

from retico.core import abstract
from retico.core.dialogue.common import DialogueActIU, DispatchableActIU
from retico.core.audio.common import DispatchedAudioIU
from retico.core.prosody.common import EndOfTurnIU
from retico.dialogue.common import AbstractDialogueManager, DialogueAct

from agents import callee, caller, agent
from networks import message

import numpy as np

class SimulatedDialogueManagerModule(abstract.AbstractModule):
    """A Simulated Dialogue Manager"""

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

    def __init__(self, agenda_file, conv_folder, agent_class, first_utterance):
        super().__init__()
        self.agenda_file = agenda_file
        self.conv_folder = conv_folder
        self.agent_class = agent_class

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
        self.fu = True
        self.ready = False
        self.rnd = random.random()

    def speak(self):
        da, fd = self.dialogue_manager.next_act()
        output_iu = self.create_iu(None)
        output_iu.set_act(da.act, da.concepts)
        output_iu.meta_data["message_data"] = fd
        output_iu.dispatch = True
        self.append(output_iu)
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

    def inverse_sigmoid(self, x):
        return -0.322581 * np.log(0.433008 * (-1 + 1/x))

    def continous_loop(self):
        while not self.dialogue_finished:
            while not self.ready:
                time.sleep(1.0)
                continue
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
            #     print("rnd", self.inverse_sigmoid(self.rnd))
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
                        if random.random() < 0.02:
                            self.speak()
                    else:
                        if self.inverse_sigmoid(self.rnd) <= self.time_until_eot():
                            iu = self.current_incoming_da
                            self.dialogue_manager.process_act(iu.act, iu.concepts)
                            self.speak()
                else:
                    if self.is_dispatching and self.interlocutor_talking:
                        output_iu = self.create_iu(None)
                        output_iu.set_act("", {})
                        output_iu.dispatch = False
                    elif not self.is_dispatching:
                        if self.inverse_sigmoid(self.rnd) <= self.time_until_eot():
                            if right_now - self.last_interl_utterance_begin < 1.5:
                                continue
                            iu = self.current_incoming_da
                            if not iu:
                                continue
                            self.dialogue_manager.process_act(iu.act, iu.concepts)
                            self.speak()
            time.sleep(0.05)

    def process_iu(self, input_iu):
        self.ready = True
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
        return None

    def setup(self):
        if isinstance(self.agent_class, str):
            agent_class = SimulatedDM.get_agent_class(self.agent_class)
        else:
            agent_class = self.agent_class

        self.dialogue_manager = SimulatedDM(self.agenda_file, self.conv_folder,
                                            agent_class)
        self.dialogue_finished = False
        t = threading.Thread(target=self.continous_loop)
        t.start()

    def shutdown(self):
        self.dialogue_finished = True


class SimulatedDM(AbstractDialogueManager):
    """A simulated dialogue manager that serves as a wrapper to the dialogue
    management used in ConvSim.
    """

    def __init__(self, agenda_file, conv_folder, agent_class):
        self.agenda_file = agenda_file
        self.conv_folder = conv_folder
        self.agent_class = agent_class
        message.MessageData.init_message_data(self.conv_folder)
        self.agent = self.agent_class(self.agenda_file, play_audio=False)

    def process_dialogue_act(self, dialogue_act):
        d = "%s:%s" % (dialogue_act.act, ",".join(dialogue_act.concepts.keys()))
        msg_data = message.MessageData(message.MessageData.NO_DATA, d)
        msg = message.Message(msg_data, None)
        self.agent.receive(msg)

    def next_act(self):
        message, _ = self.agent.act_out_turn()
        print(message.message_data.full_tag)
        print(message.speech_act.value, message.parameters)
        act = message.speech_act.value
        parameters = message.parameters
        params = {}
        for p in parameters:
            params[p] = ""
        print("%s: %s - %s" % (self.agent.name(), act, params))
        return DialogueAct(act, params), message.message_data.full_tag

    @staticmethod
    def get_agent_class(agent_type):
        """Returns the class of a ConvSim agent given its type.

        If the given agent_type is not recognized, an agent of type agent.Agent
        is returned.

        Args:
            agent_type (str): The type of the agent. Might be "caller", "callee"
                 or "agent".

        Returns:
            (agent.Agent) An agent of the specified type
        """
        if agent_type == "caller":
            return caller.Caller
        elif agent_type == "callee":
            return callee.Callee
        return agent.Agent


if __name__ == '__main__':
    sdm = SimulatedDM("data/calleefile.ini", "data/sct11", caller.Caller)
    sdm.process_act("request_info", {"num_of_persons": None})
    print(sdm.next_act())
