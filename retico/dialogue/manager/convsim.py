"""
This module uses the ConvSim conversational simulator agents for dialogue
management
"""

from retico.dialogue.common import AbstractDialogueManager

# Ugly imports from ConvSim
from agents import callee, caller, agent
from networks import message


class ConvSimDialogueManager(AbstractDialogueManager):
    """A simulated dialogue manager that serves as a wrapper to the dialogue
    management used in ConvSim.
    """

    def __init__(self, agenda_file, conv_folder, agent_class):
        self.agenda_file = agenda_file
        self.conv_folder = conv_folder
        self.agent_class = agent_class
        message.MessageData.init_message_data(self.conv_folder)
        self.agent = self.agent_class(self.agenda_file, play_audio=False)

    def process_act(self, act, concepts):
        d = "%s:%s" % (act, ",".join(concepts.keys()))
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
        return act, params

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
    sdm = ConvSimDialogueManager("data/sct11/calleefile.ini",
                                 "data/sct11/audio",
                                 agent.callee)
    sdm.process_act("request_info", {"num_of_persons": None})
    print(sdm.next_act())
