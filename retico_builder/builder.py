from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.listview import ListItemButton
from kivy.properties import ObjectProperty
from kivy.adapters.listadapter import ListAdapter
from kivy.graphics import Line, Color, InstructionGroup, Triangle
from kivy.clock import Clock

from retico_builder import modules

class ReticoApp(App):
    def build(self):
        rb = ReticoBuilder()
        Clock.schedule_interval(rb.line_drawer, 1.0/60.0)
        return rb


class ReticoBuilder(Widget):

    def line_drawer(self, dt):
        self.line_ig.clear()
        self.line_ig.add(Color(0, 0, 0, 0.8))
        for in_mod, out_mod in self.connection_list:
            self.line_ig.add(Line(points=[in_mod.ids.layout.x - 15,
                             in_mod.ids.layout.y + 245,
                             out_mod.ids.layout.x + 300,
                             out_mod.ids.layout.y + 245], width=2))
            self.line_ig.add(Triangle(points=[in_mod.ids.layout.x,
                                              in_mod.ids.layout.y + 245,
                                              in_mod.ids.layout.x - 15,
                                              in_mod.ids.layout.y + 255,
                                              in_mod.ids.layout.x - 15,
                                              in_mod.ids.layout.y + 235]))
        for module in self.module_list:
            if module.ids.layout.x < 0:
                module.ids.layout.x = 0
            if module.ids.layout.y < 0:
                module.ids.layout.y = 0

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.module_list = []
        self.connection_list = []
        self.line_ig = InstructionGroup()
        self.ids.module_pane.canvas.add(self.line_ig)
        self.connecting = None

    def add_module(self, module_name):
        w = modules.AVAILABLE_MODULES[module_name](retico_builder=self)
        self.module_list.append(w)
        layout = self.ids.module_pane.parent.parent
        w.ids.layout.center = (-layout.x + (layout.parent.width / 2),
                               -layout.y + (layout.parent.height / 2))
        self.ids.module_pane.add_widget(w)

    def delete_module(self, module):
        self.module_list.remove(module)
        self.ids.module_pane.remove_widget(module)
        ncl = []
        for a, b in self.connection_list:
            if a is not module and b is not module:
                ncl.append((a, b))
        self.connection_list = ncl

    def connect_module(self, module, in_out):
        if not self.connecting:
            self.connecting = module
            for m in self.module_list:
                if m is not module:
                    if in_out == "in":
                        m.output_connection_indicator(module.module.input_ius())
                    else:
                        m.input_connection_indicator(module.module.output_iu())
        elif self.connecting == module:
            self.connecting = None
            for m in self.module_list:
                m.reset_connection_indicator()
        else:
            if in_out == "in":
                in_mod = module
                out_mod = self.connecting
            else:
                in_mod = self.connecting
                out_mod = module
            self.connection_list.append((in_mod, out_mod))
            out_mod.module.subscribe(in_mod.module)
            self.connecting = None
            for m in self.module_list:
                m.reset_connection_indicator()

    def run(self):
        for m in self.module_list:
            m.setup()
        for m in self.module_list:
            m.run()

    def stop(self):
        for m in self.module_list:
            m.stop()


class ModulePane(Widget):
    pass


class MyListItemButton(ListItemButton):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.height = 40


class MenuWidget(Widget):

    module_list = ObjectProperty()
    module_list_adapter = ObjectProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.list_adapter = ListAdapter(data=modules.AVAILABLE_MODULES.keys(),
                                        cls=MyListItemButton)

    def add_module(self):
        if self.list_adapter.selection:
            self.parent.add_module(self.list_adapter.selection[0].text)

    def run(self):
        self.ids.run_button.disabled = True
        self.ids.stop_button.disabled = False
        self.parent.run()

    def stop(self):
        self.ids.run_button.disabled = False
        self.ids.stop_button.disabled = True
        self.parent.stop()


def main():
    print("Hello World")
    ReticoApp().run()

if __name__ == '__main__':
    main()
