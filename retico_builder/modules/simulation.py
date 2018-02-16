"""A module for simulation module widgets."""

from retico.modules.simulation import asr, dm, eot, nlg, nlu, tts
from retico_builder.modules.abstract import InfoLabelWidget


class SimulatedASRWidget(InfoLabelWidget):
    """A simulated ASR module."""

    retico_class = asr.SimulatedASRModule

    def update_info(self):
        iu = self.module.latest_iu()
        if iu:
            self.info_label.text = iu.get_text()


class SimulatedDialogueManagerWidget(InfoLabelWidget):
    """A simulated ASR module."""

    retico_class = dm.SimulatedDialogueManagerModule
    args = {"agenda_file": "data/callerfile.ini",
            "conv_folder": "data/sct11",
            "agent_class": "caller",
            "first_utterance": True}

    def update_info(self):
        iu = self.module.latest_iu()
        if iu:
            self.info_label.text = "%s - %s (%s)" % (iu.act, iu.concepts,
                                                     iu.dispatching)


class SimulatedEOTWidget(InfoLabelWidget):
    """A simulated EOT module."""

    retico_class = eot.SimulatedEoTModule

    def update_info(self):
        iu = self.module.latest_iu()
        if iu:
            self.info_label.text = "%s (%s)" % (iu.probability, iu.is_speaking)


class SimulatedNLGWidget(InfoLabelWidget):
    """A simulated NLG module."""

    retico_class = nlg.SimulatedNLGModule
    args = {"data_directory": "data/sct11"}

    def update_info(self):
        iu = self.module.latest_iu()
        if iu:
            self.info_label.text = "%s (%s)" % (iu.get_text(),
                                                iu.is_dispatching)

class SimulatedNLUWidget(InfoLabelWidget):
    """A simulated NLU module."""

    retico_class = nlu.SimulatedNLUModule

    def update_info(self):
        iu = self.module.latest_iu()
        if iu:
            self.info_label.text = "%s (%s)" % (iu.act, iu.concepts)

class SimulatedTTSWidget(InfoLabelWidget):
    """A simulated EOT module."""

    retico_class = tts.SimulatedTTSModule

    def update_info(self):
        iu = self.module.latest_iu()
        if iu:
            self.info_label.text = str(iu.dispatch)
