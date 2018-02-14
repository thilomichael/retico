import time
import threading

from kivy.uix.widget import Widget
from kivy.uix.behaviors import DragBehavior
from kivy.uix.button import Button

from retico.core.debug.general import CallbackModule
from retico.core.abstract import AbstractModule, AbstractProducingModule, AbstractConsumingModule
from retico.core.audio.io import SpeakerModule, MicrophoneModule, AudioRecorderModule, AudioDispatcherModule
from retico.modules.google.asr import GoogleASRModule
from retico.modules.rasa.nlu import RasaNLUModule
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label

class ModuleWidget(Widget, DragBehavior):

    retico_class = AbstractModule
    args = {}

    def popup_callback(self, instance):
        thing = eval(self.popup_content.text)
        self.args = thing
        self.module = self.retico_class(**thing)
        self.ids.title.text = self.module.name()
        self.reset_connection_indicator()

    def show_popup(self):
        std_text = str(self.args)
        self.popup_content = TextInput(text=std_text)
        popup = Popup(title="Arguments", content=self.popup_content,
                      size_hint=(None, None), size=(400, 400))
        popup.bind(on_dismiss=self.popup_callback)
        popup.open()

    def __init__(self, retico_builder=None, retico_args=None, retico_class=None,
                 show_popup=True, **kwargs):
        super().__init__(**kwargs)
        self.retico_builder = retico_builder
        self.is_running = False
        if retico_class:
            self.retico_class = retico_class
        if retico_args:
            self.args = retico_args

        if self.args and show_popup:
            self.show_popup()
            self.module = None
        else:
            self.module = self.retico_class(**self.args)
            self.ids.title.text = self.module.name()
            self.reset_connection_indicator()

    def in_button_pressed(self):
        self.ids.out_button.disabled = True
        self.ids.in_button.background_color = (0.9, 0.9, 0.8, 1)
        self.retico_builder.connect_module(self, "in")

    def out_button_pressed(self):
        self.ids.in_button.disabled = True
        self.ids.out_button.background_color = (0.9, 0.9, 0.8, 1)
        self.retico_builder.connect_module(self, "out")

    def del_button_pressed(self):
        self.retico_builder.delete_module(self)

    def reset_connection_indicator(self):
        self.ids.out_button.background_color = (0.6, 0.8, 0.6, 1)
        self.ids.in_button.background_color = (0.6, 0.8, 0.6, 1)
        self.ids.out_button.disabled = False
        self.ids.in_button.disabled = False
        if isinstance(self.module, AbstractConsumingModule):
            self.ids.out_button.disabled = True
        elif isinstance(self.module, AbstractProducingModule):
            self.ids.in_button.disabled = True

    def input_connection_indicator(self, iu_type):
        may_connect = False
        self.ids.out_button.disabled = True
        if self.ids.in_button.disabled:
            return
        for valid_type in self.module.input_ius():
            if issubclass(iu_type, valid_type):
                may_connect = True
        if not may_connect:
            self.ids.in_button.disabled = True

    def setup(self):
        self.module.setup()

    def update_info(self):
        pass

    def _run(self):
        self.is_running = True
        while self.is_running:
            self.update_info()
            time.sleep(0.1)

    def run(self):
        t = threading.Thread(target=self._run)
        t.start()
        self.module.run(run_setup=False)

    def stop(self):
        self.module.stop()
        self.is_running = False

    def output_connection_indicator(self, iu_types):
        may_connect = False
        self.ids.in_button.disabled = True
        if self.ids.out_button.disabled:
            return
        for available_type in iu_types:
            if issubclass(self.module.output_iu(), available_type):
                may_connect = True
        if not may_connect:
            self.ids.out_button.disabled = True

class InfoLabelWidget(ModuleWidget):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.info_label = Label()
        self.info_label.text = "Info"
        self.ids.mc.add_widget(self.info_label)
        self.info_label.size = (300, 250)
        self.info_label.center = (150, 150)
        self.info_label.font_size = 15
        self.info_label.halign = 'center'
        self.info_label.valign = 'middle'
        self.info_label.color = (0, 0, 0, 1)


class DebugModuleWidget(InfoLabelWidget):

    retico_class = CallbackModule

    def callback(self, input_iu):
        self.info_label.text = str(input_iu.payload)

    def __init__(self, **kwargs):
        super().__init__(retico_args={"callback": self.callback},
                         show_popup=False,
                         **kwargs)

class SpeakerModuleWidget(ModuleWidget):

    retico_class = SpeakerModule

class MicrophoneModuleWidget(ModuleWidget):

    retico_class = MicrophoneModule
    args = {"chunk_size": 5000}

class GoogleASRModuleWidget(InfoLabelWidget):

    retico_class = GoogleASRModule
    args = {"language": "en-US", "nchunks": 20}

    def update_info(self):
        iu = self.module.latest_iu()
        if iu:
            self.info_label.text = iu.get_text()

class RasaNLUModuleWidget(InfoLabelWidget):

    retico_class = RasaNLUModule
    args = {"model_dir": "data/rasa/models/nlu/current",
            "config_file": "data/rasa/nlu_model_config.json"}

    def update_info(self):
        iu = self.module.latest_iu()
        if iu:
            self.info_label.text = "%s - %s" % (iu.act, iu.concepts)

class AudioRecorderModuleWidget(ModuleWidget):

    retico_class = AudioRecorderModule
    args = {"filename": "recording.wav"}

class AudioDispatcherModuleWidget(ModuleWidget):

    retico_class = AudioDispatcherModule
    args = {"target_chunk_size": 5000}
