"""A Module for an agenda based dialogue manager."""

import configparser
from retico.dialogue.common import AbstractDialogueManager


class AgendaBasedDialogueManager(AbstractDialogueManager):
    """An agenda based dialogue manager."""

    def process_dialogue_act(self, dialogue_act):
        pass

    def next_act(self):
        pass

    def __init__(self, agenda_file):
        self.agenda_file = agenda_file
        self.config = configparser.ConfigParser(allow_no_value=True)
        self.config.read(agenda_file)

    def create_agenda(self, agenda_file):
        """Loads required and available concepts from an ini-file and creates an
        agenda that will be used by the dialogue manager.

        Args:
            agenda_file (str): Path to the agenda file that should be loaded.
        """
        pass
