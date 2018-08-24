from retico.modules.simulation import dm
from retico.dialogue.manager.rasa import RasaDialogueManager, RandomChoicePolicy


class RasaDialogueManagerModule(dm.SimulatedDialogueManagerModule):
    "An n-gram dialogue manager module"

    @staticmethod
    def name():
        return "RASA (LSTM-RNN) DM Module"

    def __init__(self, model_dir, first_utterance, **kwargs):
        super().__init__(first_utterance, **kwargs)
        self.model_dir = model_dir
        self.first_utterance = first_utterance
        self.dialogue_manager = RasaDialogueManager(model_dir)
