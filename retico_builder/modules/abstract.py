from flexx import flx
import time

import json
import threading
import asyncio

class AbstractModule(flx.PyComponent):

    MODULE = flx.PyComponent
    PARAMETERS = {}

    def update_running_info(self):
        latest_iu = self.retico_module.latest_iu()
        if latest_iu:
            self.gui.update_info("Latest IU:<br>%s" % latest_iu)

    def set_content(self):
        pass

    def init(self, gui, parameters):
        self.retico_module = self.MODULE(**json.loads(parameters))
        self.gui = gui
        self.set_content()
        self.running = False

    def enable_output_iu(self, out_iu):
        if any([issubclass(out_iu, in_iu) for in_iu in self.MODULE.input_ius()]):
            self.gui.enable_input_buttons()
            self.gui.highlight(True)
        else:
            self.gui.disable_input_buttons()
            self.gui.highlight(False)
        self.gui.disable_output_buttons()

    def enable_input_ius(self, in_ius):
        if any([issubclass(self.MODULE.output_iu(), in_iu) for in_iu in in_ius]):
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

    def setup(self):
        self.gui.setup()
        time.sleep(0.1)
        self.retico_module.setup()
        time.sleep(0.1)
        self.gui.highlight(True, "border")

    def run(self):
        self.retico_module.run(run_setup=False)

    def stop(self):
        self.enable_buttons()
        time.sleep(0.1)
        self.gui.stop()
        self.retico_module.stop()
