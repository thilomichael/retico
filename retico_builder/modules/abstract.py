from flexx import flx

import json

class AbstractModule(flx.PyComponent):

    MODULE = None
    PARAMETERS = {}

    def get_content(self):
        return []

    def init(self, gui, parameters):
        self.retico_module = self.MODULE(**json.loads(parameters))
        self.gui = gui
        self.gui.set_content(self.get_content())

    def enable_output_iu(self, out_iu):
        if out_iu in self.MODULE.input_ius():
            self.gui.enable_input_buttons()
            self.gui.highlight(True)
        else:
            self.gui.disable_input_buttons()
            self.gui.highlight(False)
        self.gui.disable_output_buttons()

    def enable_input_ius(self, in_ius):
        if self.MODULE.output_iu() in in_ius:
            self.gui.enable_output_buttons()
            self.gui.highlight(True)
        else:
            self.gui.disable_output_buttons()
            self.gui.highlight(False)
        self.gui.disable_input_buttons()

    def enable_buttons(self):
        if self.MODULE.input_ius():
            self.gui.enable_input_buttons()
        else:
            self.gui.disable_input_buttons()
        if self.MODULE.output_iu():
            self.gui.enable_output_buttons()
        else:
            self.gui.disable_output_buttons()
        self.gui.highlight(False)
