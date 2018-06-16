from flexx import flx
from retico_builder.modules.abstract import AbstractModule

try:
    from retico.modules.rasa import nlu

    class RasaNLUModule(AbstractModule):

        MODULE = nlu.RasaNLUModule
        PARAMETERS = {"model_dir": "data/rasa/models/nlu/current", "config_file": "data/rasa/nlu_model_config.json"}

        def set_content(self):
            self.gui.clear_content()
            self.gui.add_info("Model dir: %s" % self.retico_module.model_dir)
            self.gui.add_info("Config file: %s" % self.retico_module.config_file)

        def update_running_info(self):
            latest_iu = self.retico_module.latest_iu()
            if latest_iu:
                self.gui.update_info("Intent: %s<br>Concept: %s" % (latest_iu.act, latest_iu.concepts))

except ImportError:
    pass
