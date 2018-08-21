
import json

from retico.core.abstract import AbstractConsumingModule
from retico.core.dialogue.common import DispatchableActIU, DialogueActIU

class DialogueActRecorderModule(AbstractConsumingModule):
    """A module that writes dispatched dialogue acts to file."""

    @staticmethod
    def name():
        return "Dialogue Act Recorder Module"

    @staticmethod
    def description():
        return "A module that writes dialogue acts into a file."

    @staticmethod
    def input_ius():
        return [DialogueActIU, DispatchableActIU]

    def __init__(self, filename, **kwargs):
        super().__init__(**kwargs)
        self.filename = filename
        self.txt_file = None

    def setup(self):
        self.txt_file = open(self.filename, "w")

    def shutdown(self):
        if self.txt_file:
            self.txt_file.close()
            self.txt_file = None

    def process_iu(self, input_iu):
        if self.txt_file:
            if isinstance(input_iu, DispatchableActIU):
                self.txt_file.write("%s\t%s\t%s\n" % (input_iu.creator,
                                    input_iu.act, json.dumps(input_iu.concepts)))
            else:
                self.txt_file.write("%s\t%s\t%s\t%s\n" % (input_iu.creator, input_iu.act,
                                                      json.dumps(input_iu.concepts),
                                                      input_iu.dispatch
                                                  ))
