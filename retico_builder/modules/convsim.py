from retico_builder.modules.abstract import AbstractModule

try:
    from retico.modules.simulation import dm_convsim

    class ConvsimDialogueManagerModule(AbstractModule):

        MODULE = dm_convsim.ConvSimDialogueManagerModule
        PARAMETERS = {"agenda_file": "data/sct11/callerfile.ini", "conv_folder": "data/sct11/audio", "agent_class": "caller", "first_utterance": False}

        def set_content(self):
            self.gui.clear_content()
            self.gui.add_info("Dialogue Manager:<br><b>%s</b>" % self.retico_module.role)
            self.gui.add_info("Agenda file: %s" % self.retico_module.agenda_file)
            self.gui.add_info("Conv folder: %s" % self.retico_module.conv_folder)
            self.gui.add_info("First utterance: %s" % self.retico_module.first_utterance)

        def update_running_info(self):
            latest_iu = self.retico_module.latest_iu()
            if latest_iu:
                self.gui.update_info("Intent: %s<br>Concept: %s" % (latest_iu.act, latest_iu.concepts))

except ImportError:
    pass
