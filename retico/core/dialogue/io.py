
import json
import time

from retico.core.abstract import AbstractConsumingModule, AbstractTriggerModule
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

    def __init__(self, filename, separator="\t", **kwargs):
        super().__init__(**kwargs)
        self.filename = filename
        self.separator = separator
        self.txt_file = None

    def setup(self):
        self.txt_file = open(self.filename, "w")

    def prepare_run(self):
        self.start_time = time.time()

    def shutdown(self):
        if self.txt_file:
            self.txt_file.close()
            self.txt_file = None

    def process_iu(self, input_iu):
        if self.txt_file:
            self.txt_file.write("dialogue_act")
            self.txt_file.write(self.separator)
            self.txt_file.write(str(input_iu.creator).split(" ")[-1])
            self.txt_file.write(self.separator)
            if input_iu.created_at < self.start_time:
                self.start_time = input_iu.created_at
            self.txt_file.write(str(int((input_iu.created_at-self.start_time)*1000)))
            self.txt_file.write(self.separator)
            self.txt_file.write("-1")
            self.txt_file.write(self.separator)
            if input_iu.concepts.keys():
                self.txt_file.write(input_iu.act+":"+",".join(input_iu.concepts.keys()))
            else:
                self.txt_file.write(input_iu.act)
            if isinstance(input_iu, DispatchableActIU):
                self.txt_file.write(self.separator)
                self.txt_file.write(str(input_iu.dispatch))
            self.txt_file.write("\n")


class DialogueActTriggerModule(AbstractTriggerModule):

    @staticmethod
    def name():
        return "Dialogue Act Trigger Module"

    @staticmethod
    def description():
        return "A trigger module that emits a dialogue act when triggered."

    @staticmethod
    def output_iu():
        return DispatchableActIU

    def __init__(self, dispatch=True, **kwargs):
        super().__init__(**kwargs)
        self.dispatch = True

    def trigger(self, data={}):
        output_iu = self.create_iu()
        output_iu.dispatch = self.dispatch
        output_iu.set_act(data.get("act", "greeting"),
                          data.get("concepts", {}))
        self.append(output_iu)
