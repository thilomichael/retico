"""
A module for the convsim dialogue manager module.
This class has its own module so that the import may be ignored when convsim is
not installed.
"""

from retico.modules.simulation import dm
from retico.dialogue.manager.convsim import ConvSimDialogueManager

class ConvSimDialogueManagerModule(dm.TurnTakingDialogueManagerModule):
    """A turn taking dialogue manager module that utilizes the convsim
    dialogue manager implemented in `retico.dialogue.manager.convsim` to generate
    dialogue acts.

    Convsim is an agenda based dialogue manager that also handles turn taking.
    However, the turn taking information is ignored by the dialogue manager and
    just the dialogue acts are returned.
    """

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
            self.agent_class = ConvSimDialogueManager.get_agent_class(agent_class)
        else:
            self.agent_class = agent_class

    def setup(self):
        super().setup()
        self.dialogue_manager = ConvSimDialogueManager(self.agenda_file,
                                                       self.conv_folder,
                                                       self.agent_class)
