from retico_builder.modules.abstract import AbstractTriggerModule
import retico.core.text.io as textio
import retico.core.dialogue.io as dialogueio

import json

class TextTriggerModule(AbstractTriggerModule):

    MODULE = textio.TextTriggerModule
    PARAMETERS = {"dispatch": True}

    def handle_trigger(self, text):
        self.retico_module.trigger({"text": text})

class DialogueActTriggerModule(AbstractTriggerModule):

    MODULE = dialogueio.DialogueActTriggerModule
    PARAMETERS = {"dispatch": True}

    def handle_trigger(self, text):
        input = json.loads(text)
        self.retico_module.trigger(input)
