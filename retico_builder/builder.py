"""The module for the gui of the retico builder."""

import pickle
import os

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.graphics import (Line, Color, InstructionGroup, Triangle, Fbo,
                           ClearColor, ClearBuffers, Rectangle)
from kivy.clock import Clock
from kivy.config import Config
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.treeview import TreeViewLabel
from kivy.uix.popup import Popup
from kivy.uix.button import Button
from kivy.core.window import Window

from retico_builder import modules


class ReticoApp(App):
    """The main application retico builder."""
    def build(self):
        Config.set('input', 'mouse', 'mouse,disable_multitouch')
        Window.size = (1000, 700)
        rb = ReticoBuilder()
        Clock.schedule_interval(rb.line_drawer, 1.0 / 60.0)
        Clock.schedule_interval(rb.minimap_drawer, 2.0)
        Clock.schedule_interval(rb.drag_guard, 1.0 / 60.0)
        menu_widget = rb.ids.menu_widget
        menu_widget.ids.minimap.bind(on_touch_down=menu_widget.minimap_touch)
        menu_widget.ids.minimap.bind(on_touch_move=menu_widget.minimap_touch)
        menu_widget.load_module_list()
        self.title = "ReTiCo Builder"
        return rb


class ReticoBuilder(Widget):
    """The main widget of the application."""

    def minimap_drawer(self, dt):
        """Updates the minimap.

        For this, a fbo is used to capture an image of the module pane widget.
        Additionally a rectangle is added where the current window is located.
        """
        thing = self.ids.module_pane
        layout = self.ids.layout
        screen = self.ids.screen

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

    def _draw_line(self, in_mod, out_mod):
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

    def line_drawer(self, dt):
        """This routine draws the arrows between the modules."""
        self.line_ig.clear()
        self.line_ig.add(Color(0, 0, 0, 0.8))
        in_dragged = []
        out_dragged = []
        for in_mod, out_mod in self.connection_list:
            if in_mod.is_dragged:
                in_dragged.append((in_mod, out_mod))
            elif out_mod.is_dragged:
                out_dragged.append((in_mod, out_mod))
            else:
                self._draw_line(in_mod, out_mod)
        self.line_ig.add(Color(0, 1, 0, 1))
        for in_mod, out_mod in in_dragged:
            self._draw_line(in_mod, out_mod)
        self.line_ig.add(Color(1, 0, 0, 1))
        for in_mod, out_mod in out_dragged:
            self._draw_line(in_mod, out_mod)

    def drag_guard(self, dt):
        """Method that continously checks if the screen or a module is out of
        bounds and enforces the bounds."""
        max_width = self.ids.module_pane.width
        max_height = self.ids.module_pane.height
        screen = self.ids.screen

        for module in self.module_list:
            if module.ids.layout.x < 0:
                module.ids.layout.x = 0
            elif module.ids.layout.x > max_width - 300:
                module.ids.layout.x = max_width - 300
            if module.ids.layout.y < 0:
                module.ids.layout.y = 0
            elif module.ids.layout.y > max_height - 300:
                module.ids.layout.y = max_height - 300
        layout = self.ids.layout

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
        """Adds a module to the module pane."""
        w = modules.AVAILABLE_MODULES[module_name](retico_builder=self,
                                                   retico_args=args,
                                                   show_popup=show_popup)
        w.bind(on_touch_down=w.touch_down)
        w.bind(on_touch_up=w.touch_up)
        self.module_list.append(w)
        layout = self.ids.layout
        screen = self.ids.screen
        w.ids.layout.center = (-layout.x + (screen.width / 2),
                               -layout.y + (screen.height / 2))
        self.ids.module_pane.add_widget(w)
        return w

    def delete_module(self, module):
        """Deletes a module."""
        self.module_list.remove(module)
        self.ids.module_pane.remove_widget(module)
        ncl = []
        for a, b in self.connection_list:
            if a is not module and b is not module:
                ncl.append((a, b))
        self.connection_list = ncl

    def connect_module(self, module, in_out):
        """Connects a module."""
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
        """Runs all modules."""
        for m in self.module_list:
            m.setup()
        for m in self.module_list:
            m.run()

    def stop(self):
        """Stops all modules."""
        for m in self.module_list:
            m.stop()

    def save(self, filename):
        """Saves the current graph to file."""
        m_list = []
        c_list = []
        for m in self.module_list:
            save_dict = {}
            save_dict["retico_class"] = m.retico_class
            save_dict["args"] = m.get_args()
            save_dict["retico_args"] = m.args
            save_dict["widget"] = str(m.__class__)
            save_dict["x"] = m.ids.layout.x
            save_dict["y"] = m.ids.layout.y
            save_dict["id"] = id(m)
            save_dict["widget_name"] = m.name()
            m_list.append(save_dict)
        for a, b in self.connection_list:
            c_list.append((id(a), id(b)))
        pickle.dump([m_list, c_list], open("%s.rtc" % filename, "wb"))

    def load(self):
        """Opens a File Chooser and loads the chosen graph."""
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
            if m.get("x") and m.get("y"):
                w.ids.layout.x = m["x"]
                w.ids.layout.y = m["y"]
            id_dict[m["id"]] = w
        for ida, idb in mc_list[1]:
            self.connection_list.append((id_dict[ida], id_dict[idb]))
            id_dict[idb].module.subscribe(id_dict[ida].module)


class MenuWidget(Widget):
    """The widget containing the menu."""

    def load_module_list(self):
        """Loads the module list and displays it in a tree view."""
        new_dict = {}
        tv = self.ids.module_list
        tv.hide_root = True
        for k, v in modules.AVAILABLE_MODULES.items():
            modname = str(v.__module__)
            if not new_dict.get(modname):
                new_dict[modname] = []
            new_dict[modname].append(k)
        for group, mlist in new_dict.items():
            label = TreeViewLabel(text="  " + group)
            label.no_selection = True
            item = tv.add_node(label)
            mlist.sort()
            for m in mlist:
                tv.add_node(TreeViewLabel(text=m.replace(" Module", "")),
                            parent=item)
        tv.size_hint = 1, None
        tv.bind(minimum_height=tv.setter('height'))

    def add_module(self):
        """Add module callback."""
        if self.ids.module_list.selected_node:
            self.parent.add_module(self.ids.module_list.selected_node.text +
                                   " Module")

    def run(self):
        """Run button callback."""
        self.ids.run_button.disabled = True
        self.ids.stop_button.disabled = False
        self.parent.run()

    def stop(self):
        """Stop button callback."""
        self.ids.run_button.disabled = False
        self.ids.stop_button.disabled = True
        self.parent.stop()

    def save(self):
        """Save button callback. Displays a message."""
        self.stop()
        if self.ids.file_field.text:
            self.parent.save(self.ids.file_field.text)

        content = Button(text='OK')
        popup = Popup(title="File was saved.", content=content, size=(400, 300),
                      size_hint=(None, None))
        content.bind(on_press=popup.dismiss)
        popup.open()

    def load(self):
        """Load button callback."""
        self.stop()
        self.parent.load()

    def minimap_touch(self, instance, touch):
        """Callback for clicks and drags on the mini map."""
        if instance.collide_point(*touch.pos):
            relativex = (touch.pos[0] - instance.x) / instance.width
            relativey = (touch.pos[1] - instance.y) / instance.height
            layout = self.parent.ids.module_pane.parent.parent
            screen = layout.parent
            layout.pos = ((-layout.width * relativex) + (screen.width / 2),
                          (-layout.width * relativey) + (screen.height / 2))
            self.parent.minimap_drawer(0)


def main():
    """Runs the retico builder."""
    ReticoApp().run()


if __name__ == '__main__':
    main()
