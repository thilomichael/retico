from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.listview import ListItemButton
from kivy.properties import ObjectProperty
from kivy.adapters.listadapter import ListAdapter
from kivy.graphics import Line, Color, InstructionGroup, Triangle, Fbo, ClearColor, ClearBuffers, Scale, Translate, Rectangle
from kivy.clock import Clock
from kivy.config import Config
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.popup import Popup
from kivy.uix.button import Button
from kivy.core.window import Window


import pickle
import threading
import time
import os

from retico_builder import modules


class ReticoApp(App):
    def build(self):
        Config.set('input', 'mouse', 'mouse,disable_multitouch')
        Window.size = (1000, 700)
        rb = ReticoBuilder()
        Clock.schedule_interval(rb.line_drawer, 1.0 / 60.0)
        Clock.schedule_interval(rb.minimap_drawer, 2.0)
        Clock.schedule_interval(rb.drag_guard, 1.0 / 60.0)
        rb.ids.menu_widget.ids.minimap.bind(on_touch_down=rb.ids.menu_widget.minimap_touch)
        rb.ids.menu_widget.ids.minimap.bind(on_touch_move=rb.ids.menu_widget.minimap_touch)
        return rb


class ReticoBuilder(Widget):

    def minimap_drawer(self, dt):
        """Updates the minimap.

        For this, a fbo is used to capture an image of the module pane widget.
        Additionally a rectangle is added where the current window is located.
        """
        # self.ids.module_pane.parent.parent.export_to_png(".mm.png")
        # self.ids.menu_widget.ids.minimap.reload()
        thing = self.ids.module_pane
        layout = self.ids.module_pane.parent.parent
        screen = thing.parent.parent.parent

        canvas_parent_index = thing.parent.canvas.indexof(thing.canvas)
        thing.parent.canvas.remove(thing.canvas)

        fbo = Fbo(size=thing.size, with_stencilbuffer=True)

        with fbo:
            ClearColor(0.85, 0.85, 0.85, 1)
            ClearBuffers()
            # Scale(1, -1, 1)
            # Translate(-thing.x, -thing.y - thing.height, 0)

        fbo.add(thing.canvas)
        fbo.add(Color(0, 0, 0, 0.3))
        fbo.add(Rectangle(pos=(-layout.x, -layout.y), size=screen.size))
        fbo.draw()
        self.ids.menu_widget.ids.minimap.texture = fbo.texture
        fbo.remove(thing.canvas)

        thing.parent.canvas.insert(canvas_parent_index, thing.canvas)

    def line_drawer(self, dt):
        """This routine draws the arrows between the modules."""
        self.line_ig.clear()
        self.line_ig.add(Color(0, 0, 0, 0.8))
        for in_mod, out_mod in self.connection_list:
            # self.line_ig.add(Line(points=[in_mod.ids.layout.x - 15,
            #                  in_mod.ids.layout.y + 245,
            #                  out_mod.ids.layout.x + 300,
            #                  out_mod.ids.layout.y + 245], width=2))
            outx = out_mod.ids.layout.x
            outy = out_mod.ids.layout.y
            inx = in_mod.ids.layout.x
            iny = in_mod.ids.layout.y
            halfx = outx + 300 + (((inx - 15) - (outx + 300)) / 2)
            halfy = outy + 245 + (((iny + 245) - (outy + 245 + 190)) / 2)

            # Draw line stubs
            self.line_ig.add(Line(points=[inx - 15,
                                          iny + 245,
                                          inx - 25,
                                          iny + 245], width=2))
            self.line_ig.add(Line(points=[outx + 300,
                                          outy + 245,
                                          outx + 310,
                                          outy + 245], width=2))
            # Draw the arrow
            self.line_ig.add(Triangle(points=[inx,
                                              iny + 245,
                                              inx - 15,
                                              iny + 255,
                                              inx - 15,
                                              iny + 235]))

            # Draw the line depending on relative position
            if outx + 300 + 30 >= inx:
                self.line_ig.add(Line(points=[outx + 310,
                                              outy + 245,
                                              outx + 310,
                                              halfy], width=2))
                self.line_ig.add(Line(points=[inx - 25,
                                              halfy,
                                              outx + 310,
                                              halfy], width=2))
                self.line_ig.add(Line(points=[inx - 25,
                                              iny + 245,
                                              inx - 25,
                                              halfy], width=2))
            else:
                self.line_ig.add(Line(points=[outx + 310,
                                              outy + 245,
                                              halfx,
                                              outy + 245], width=2))
                self.line_ig.add(Line(points=[halfx,
                                              outy + 245,
                                              halfx,
                                              iny + 245], width=2))
                self.line_ig.add(Line(points=[halfx,
                                              iny + 245,
                                              inx - 25,
                                              iny + 245], width=2))

    def drag_guard(self, dt):
        max_width = self.ids.module_pane.width
        max_height = self.ids.module_pane.height
        screen = self.ids.module_pane.parent.parent.parent

        for module in self.module_list:
            if module.ids.layout.x < 0:
                module.ids.layout.x = 0
            elif module.ids.layout.x > max_width - 300:
                module.ids.layout.x = max_width - 300
            if module.ids.layout.y < 0:
                module.ids.layout.y = 0
            elif module.ids.layout.y > max_height - 300:
                module.ids.layout.y = max_height - 300
        layout = self.ids.module_pane.parent.parent

        if layout.x > 300:
            layout.x = 300
        elif layout.x < -max_width + screen.width - 300:
            layout.x = -max_width + screen.width - 300
        if layout.y > 300:
            layout.y = 300
        elif layout.y < -max_height + screen.height - 300:
            layout.y = -max_height + screen.height - 300

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.module_list = []
        self.connection_list = []
        self.line_ig = InstructionGroup()
        self.ids.module_pane.canvas.add(self.line_ig)
        self.connecting = None
        self.exit = False

    def add_module(self, module_name, args=None, show_popup=True):
        w = modules.AVAILABLE_MODULES[module_name](retico_builder=self,
                                                   retico_args=args,
                                                   show_popup=show_popup)
        self.module_list.append(w)
        layout = self.ids.module_pane.parent.parent
        w.ids.layout.center = (-layout.x + (layout.parent.width / 2),
                               -layout.y + (layout.parent.height / 2))
        self.ids.module_pane.add_widget(w)
        return w

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

    def save(self, filename):
        m_list = []
        c_list = []
        for m in self.module_list:
            save_dict = {}
            save_dict["retico_class"] = m.retico_class
            save_dict["args"] = m.get_args()
            save_dict["widget"] = m.__class__
            save_dict["x"] = m.ids.layout.x
            save_dict["y"] = m.ids.layout.y
            save_dict["id"] = id(m)
            save_dict["widget_name"] = m.name()
            m_list.append(save_dict)
        for a, b in self.connection_list:
            c_list.append((id(a), id(b)))
        pickle.dump([m_list, c_list], open("%s.rtc" % filename, "wb"))

    def load(self):
        fc = FileChooserListView()
        fc.path = os.getcwd()
        popup = Popup(title="Load", content=fc)
        fc.fbind('selection', popup.dismiss)
        popup.bind(on_dismiss=self._load_callback)
        popup.open()

    def _load_callback(self, instance):
        if not instance.content.selection:
            return
        filename = instance.content.selection[0]
        print(filename)
        self.module_list = []
        self.connection_list = []
        self.ids.module_pane.clear_widgets()
        mc_list = pickle.load(open(filename, "rb"))
        id_dict = {}
        for m in mc_list[0]:
            w = self.add_module(m["widget_name"], args=m["args"],
                                show_popup=False)
            w.ids.layout.x = m["x"]
            w.ids.layout.y = m["y"]
            id_dict[m["id"]] = w
        for ida, idb in mc_list[1]:
            self.connection_list.append((id_dict[ida], id_dict[idb]))
            id_dict[idb].module.subscribe(id_dict[ida].module)



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
        data = []
        data.extend(modules.AVAILABLE_MODULES.keys())
        self.list_adapter = ListAdapter(data=data,
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

    def save(self):
        self.stop()
        if self.ids.file_field.text:
            self.parent.save(self.ids.file_field.text)

        content = Button(text='OK')
        popup = Popup(title="File was saved.", content=content, size=(400, 300),
                      size_hint=(None, None))
        content.bind(on_press=popup.dismiss)
        popup.open()

    def load(self):
        self.stop()
        self.parent.load()

    def minimap_touch(self, instance, touch):
        if instance.collide_point(*touch.pos):
            relativex = (touch.pos[0] - instance.x) / instance.width
            relativey = (touch.pos[1] - instance.y) / instance.height
            layout = self.parent.ids.module_pane.parent.parent
            screen = layout.parent
            print(layout.size)
            layout.pos = ((-layout.width * relativex) + (screen.width/2),
                          (-layout.width * relativey) + (screen.height/2))
            # print(relativex, relativey)
            self.parent.minimap_drawer(0)


def main():
    print("Hello World")
    ReticoApp().run()


if __name__ == '__main__':
    main()