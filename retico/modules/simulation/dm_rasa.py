"""
A Module for the rasa dialogue manager module.
This class has its own module so that the import may be ignored when rasa is not
installed.
"""

from retico.modules.simulation import dm
from retico.dialogue.manager.rasa import RasaDialogueManager, RandomChoicePolicy


class RasaDialogueManagerModule(dm.TurnTakingDialogueManagerModule):
    """A turn taking dialogue manager module that utilizes the rasa_core engine
    dialogue manager implemented in `retico.dialogue.manager.rasa` to generate
    dialogue acts. Rasa uses recurrent neural network to predict actions based
    on intents and entities given to the system.

    Because rasas dialogue structure is static (the "user" may only ever utter
    one dialogue act before that systems outputs 0..n dialogue acts) this
    approach does not work that well...
    """

    @staticmethod
    def name():
        return "RASA (LSTM-RNN) DM Module"

    def __init__(self, model_dir, first_utterance, **kwargs):
        super().__init__(first_utterance, **kwargs)
        self.model_dir = model_dir
        self.first_utterance = first_utterance

    def setup(self):
        super().setup()
        self.dialogue_manager = RasaDialogueManager(self.model_dir)
