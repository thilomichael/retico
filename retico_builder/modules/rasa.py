"""A module for rasa widgets."""

from retico_builder.modules.abstract import InfoLabelWidget

try:
    from retico.modules.rasa.nlu import RasaNLUModule

    class RasaNLUModuleWidget(InfoLabelWidget):
        """A widget for NLU by rasa."""

        retico_class = RasaNLUModule
        args = {"model_dir": "data/rasa/models/nlu/current",
                "config_file": "data/rasa/nlu_model_config.json"}

        def update_info(self):
            iu = self.module.latest_iu()
            if iu:
                self.info_label.text = "%s - %s" % (iu.act, iu.concepts)
except ImportError:
    pass
