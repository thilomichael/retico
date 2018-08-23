from retico_builder.modules.abstract import AbstractModule, AbstractTriggerModule
from retico.core.text import asr
from retico.core.dialogue import io
from retico.core.text import io as textio

class TextDispatcherModule(AbstractModule):

    MODULE = asr.TextDispatcherModule
    PARAMETERS = {"forward_after_final": True}

    def set_content(self):
        self.gui.clear_content()
        self.gui.add_info("Text Dispatcher Module")

    def update_running_info(self):
        latest_iu = self.retico_module.latest_iu()
        if latest_iu:
            self.gui.update_info("Current text:<br>%s" % latest_iu.payload)

class IncrementalizeASRModule(AbstractModule):

    MODULE = asr.IncrementalizeASRModule
    PARAMETERS = {"threshold": 0.8}

    def set_content(self):
        self.gui.clear_content()
        self.gui.add_info("Incrementalize ASR Module")

    def update_running_info(self):
        latest_iu = self.retico_module.latest_iu()
        if latest_iu:
            self.gui.update_info("Current text:<br>%s" % latest_iu.payload)

class DialogueActRecorderModule(AbstractModule):

    MODULE = io.DialogueActRecorderModule
    PARAMETERS = {"filename": "acts.txt"}

    def set_content(self):
        self.gui.clear_content()
        self.gui.add_info("Filename: %s" % self.retico_module.filename)

    def update_running_info(self):
        latest_iu = self.retico_module.latest_iu()
        if latest_iu:
            self.gui.update_info("Current act:<br>%s" % latest_iu.act)

class TextRecorderModule(AbstractModule):

    MODULE = textio.TextRecorderModule
    PARAMETERS = {"filename": "transcript.txt"}

    def set_content(self):
        self.gui.clear_content()
        self.gui.add_info("Filename: %s" % self.retico_module.filename)

    def update_running_info(self):
        latest_iu = self.retico_module.latest_iu()
        if latest_iu:
            self.gui.update_info("Current text:<br>%s" % latest_iu.get_text())
