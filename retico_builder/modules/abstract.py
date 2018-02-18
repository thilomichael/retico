"""A python module containing the abstract module widget definitions."""

import time
import threading
import pprint

from retico.core import abstract

from kivy.uix.widget import Widget
from kivy.uix.behaviors import DragBehavior
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput


class ModuleWidget(Widget, DragBehavior):
    """An abstract module handling the visualization of the module itself and
    the connection to other modules."""

    retico_class = abstract.AbstractModule
    args = {}

    def touch_down(self, instance, touch):
        if self.ids.layout.collide_point(*touch.pos):
            self.is_dragged = True

    def touch_up(self, instance, touch):
        if self.ids.layout.collide_point(*touch.pos):
            self.is_dragged = False

    @classmethod
    def name(cls):
        """The name of the widget."""
        try:
            return cls.retico_class.name()
        except NotImplementedError:
            return cls.__name__

    def get_args(self):
        return self.args

    def popup_callback(self, instance):
        thing = eval(self.popup_content.text)
        self.args = thing
        self.module = self.retico_class(**thing)
        self.ids.title.text = self.module.name()
        self.reset_connection_indicator()

    def show_popup(self):
        pp = pprint.PrettyPrinter(indent=4)
        std_text = pp.pformat(self.args)
        self.popup_content = TextInput(text=std_text)
        self.popup_content.font_name = "Inconsolata"
        popup = Popup(title="Arguments", content=self.popup_content,
                      size_hint=(None, None), size=(1000, 800))
        popup.bind(on_dismiss=self.popup_callback)
        popup.open()

    def __init__(self, retico_builder=None, retico_args=None, retico_class=None,
                 show_popup=True, **kwargs):
        super().__init__(**kwargs)
        self.retico_builder = retico_builder
        self.is_running = False
        self.is_dragged = False
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
        if isinstance(self.module, abstract.AbstractConsumingModule):
            self.ids.out_button.disabled = True
        elif isinstance(self.module, abstract.AbstractProducingModule):
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
    """A widget containing an info label. This label may be accessed by the
    update_info method by referencing self.info_label."""

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
