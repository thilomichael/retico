from flexx import flx
import time

import json

class AbstractModule(flx.PyComponent):

    MODULE = flx.PyComponent
    PARAMETERS = {}

    def update_running_info(self):
        latest_iu = self.retico_module.latest_iu()
        if latest_iu:
            self.gui.update_info("Latest IU:<br>%s" % latest_iu)

    def set_content(self):
        pass

    def init(self, gui, parameters, retico_module):
        if not retico_module:
            self.retico_module = self.MODULE(**json.loads(parameters))
        else:
            self.retico_module = retico_module
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
        values = []
        for in_iu in in_ius:
            oiu = self.MODULE.output_iu()
            if oiu:
                values.append(issubclass(oiu, in_iu))
        if any(values):
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
        if not self.gui.active:
            return
        self.gui.setup()
        time.sleep(0.01)
        self.retico_module.setup()
        time.sleep(0.01)
        self.gui.highlight(True, "border")

    def run(self):
        if not self.gui.active:
            return
        self.retico_module.run(run_setup=False)

    def stop(self):
        if not self.gui.active:
            return
        self.enable_buttons()
        time.sleep(0.01)
        self.gui.stop()
        self.retico_module.stop()


class AbstractTriggerModule(AbstractModule):

    def set_content(self):
        self.gui.create_trigger()

    def update_running_info(self):
        pass

    def handle_trigger(self, text):
        raise NotImplementedError()
