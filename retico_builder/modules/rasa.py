from retico_builder.modules.abstract import AbstractModule

try:
    from retico.modules.rasa import nlu
    from retico.modules.simulation import dm_rasa

    class RasaNLUModule(AbstractModule):

        MODULE = nlu.RasaNLUModule
        PARAMETERS = {
            "model_dir": "data/rasa/models/nlu/default/current",
            "incremental": False,
        }

        def set_content(self):
            self.gui.clear_content()
            self.gui.add_info("Model dir: %s" % self.retico_module.model_dir)
            self.gui.add_info("Incremental input: %s" % self.retico_module.incremental)

        def update_running_info(self):
            latest_iu = self.retico_module.latest_iu()
            if latest_iu:
                self.gui.update_info(
                    "Intent: %s<br>Concept: %s" % (latest_iu.act, latest_iu.concepts)
                )

    class RasaDialogueManagerModule(AbstractModule):

        MODULE = dm_rasa.RasaDialogueManagerModule
        PARAMETERS = {
            "model_dir": "data/sct11/rasa_models/caller/",
            "first_utterance": False,
        }

        def set_content(self):
            self.gui.clear_content()
            self.gui.add_info(
                "Dialogue Manager:<br><b>%s</b>" % self.retico_module.role
            )
            self.gui.add_info("Model directory: %s" % self.retico_module.model_dir)
            self.gui.add_info(
                "First utterance: %s" % self.retico_module.first_utterance
            )

        def update_running_info(self):
            latest_iu = self.retico_module.latest_iu()
            if latest_iu:
                self.gui.update_info(
                    "Intent: %s<br>Concept: %s" % (latest_iu.act, latest_iu.concepts)
                )


except ImportError:
    pass
