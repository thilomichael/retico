from retico.modules.simulation import dm
from retico.dialogue.manager.convsim import ConvSimDialogueManager

class ConvSimDialogueManagerModule(dm.SimulatedDialogueManagerModule):
    "A dialogue manager based on ConvSim"

    @staticmethod
    def name():
        return "ConvSim Agenda DM Module"

    def __init__(self, agenda_file, conv_folder, agent_class, first_utterance,
                 **kwargs):
        super().__init__(first_utterance, **kwargs)
        self.agenda_file = agenda_file
        self.conv_folder = conv_folder
        self.agent_class = agent_class
        self.first_utterance = first_utterance
        if isinstance(agent_class, str):
            agent_class = ConvSimDialogueManager.get_agent_class(agent_class)
        else:
            agent_class = agent_class

        self.dialogue_manager = ConvSimDialogueManager(agenda_file, conv_folder,
                                                       agent_class)
