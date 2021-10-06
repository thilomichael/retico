"""The module for the gui of the retico builder."""

import json
import glob

import base64

base64.encodestring = base64.encodebytes
base64.decodestring = base64.decodebytes

from flexx import flx
from pscript import window

from retico_builder import modlist
from retico_builder import resourceserver
from retico import headless

# Evil hack because rasa can't load self defined policies if they are not
# directly accessible in the path
try:
    from retico.dialogue.manager.rasa import RandomChoicePolicy
except ImportError:
    pass

flx.assets.associate_asset(__name__, "http://localhost:8000/interact.js")
flx.assets.associate_asset(__name__, "http://localhost:8000/style.css")


class ReticoBuilder(flx.PyComponent):
    """The main connection between the GUI (JS) and the Model (Python).
    The ReticoBuilder object lives on the Python-side and has access to all
    interfaces of the Javascript-side."""

    connecting_state = flx.BoolProp(settable=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.connecting_module = None
        self.connecting_direction = None
        self.load_map = {}
        self.load_c_list = []

    def init(self):
        module_list = modlist.get_module_list()
        file_list = glob.glob("save/*.rtc")
        self.widget = ReticoWidget(self, module_list, file_list)
        self.modules = {}
        self.running = False
        self.set_connecting_state(False)
        self.connecting_module = None
        self.connecting_direction = None

    @flx.action
    def register_module(self, module_type, parent, gui, params):
        """Creates a new module model with the given type and parameters and
        gives the model a reference to the GUI object (ReticoModule) that the
        module is representing.

        Params:
            module_type (str): The name of the class of the module that should
                be instantiated.
            parent (str): The parent name in the module list (e.g. ReTiCo,
                Google, ...)
            gui (ReticoModule): A retico module gui widget that represents the
                new module.
            params (dict): A json string of parameters that the retico module
                should be initialized with.
        """
        if self.running:
            gui.set_parent(None)
            gui.dispose()
            return
        pymodule = modlist.MODULE_LIST[parent][module_type](
            gui, params, None, flx_session=self.session
        )
        self.modules[id(gui)] = pymodule
        gui.set_mtitle(pymodule.retico_module.name())
        pymodule.enable_buttons()

    @flx.action
    def create_parameter_dialogue(self, module_type, parent):
        """Creates a parameters dialogue for the given module type.

        Before showing the dialogue, this method retrieves the default parameter
        for the module so that the parameter dialogue shows a  default.

        Params:
            module_type (str): The name of the class of the module
            parent (str): The parent name in the module list (e.g. ReTiCo, ...)
        """
        params = json.dumps(modlist.MODULE_LIST[parent][module_type].PARAMETERS)
        self.widget.create_dialogue(params, module_type, parent)

    @flx.action
    def init_out_click(self, gui):
        if (
            self.running
        ):  # If the network is in running state we do not allow to make new connections
            return
        module = self.modules[id(gui)]
        out_iu = module.MODULE.output_iu()

        self.set_connecting_state(True)
        self.connecting_module = gui
        self.connecting_direction = "out"

        gui.highlight(True, "border")
        for m in self.modules.values():
            if gui != m.gui:
                m.enable_output_iu(out_iu)

    @flx.action
    def init_in_click(self, gui):
        if (
            self.running
        ):  # If the network is in running state we do not allow to make new connections
            return
        module = self.modules[id(gui)]
        in_ius = module.MODULE.input_ius()

        self.set_connecting_state(True)
        self.connecting_module = gui
        self.connecting_direction = "in"

        gui.highlight(True, "border")
        for m in self.modules.values():
            if gui != m.gui:
                m.enable_input_ius(in_ius)

    @flx.action
    def connect_to(self, gui):
        if self.running:
            return
        if gui != self.connecting_module:
            if self.connecting_direction == "in":
                in_module = self.modules[id(self.connecting_module)]
                out_module = self.modules[id(gui)]
            else:
                in_module = self.modules[id(gui)]
                out_module = self.modules[id(self.connecting_module)]

            out_module.retico_module.subscribe(in_module.retico_module)
            self.widget.add_connection(out_module.gui, in_module.gui)

        self.set_connecting_state(False)
        self.connecting_module = None
        self.connecting_direction = None

        for m in self.modules.values():
            m.enable_buttons()

    @flx.action
    def delete_module(self, gui):
        if self.running:
            return
        self.widget.delete_module(gui)
        self.modules[id(gui)].retico_module.remove()
        del self.modules[id(gui)]
        self.set_connecting_state(False)
        self.connecting_module = None
        self.connecting_direction = None

        for m in self.modules.values():
            m.enable_buttons()

        gui.set_parent(None)
        gui.dispose()

    @flx.action
    def run(self):
        self.running = True
        self.widget.set_running("yellow")
        for m in self.modules.values():
            m.setup()

        self.widget.set_running("red")
        for m in self.modules.values():
            print("Running", m.retico_module)
            m.run()

    @flx.action
    def stop(self):
        self.running = False
        self.widget.set_running(None)
        for m in self.modules.values():
            m.stop()

    @flx.action
    def update_module_info(self):
        for m in self.modules.values():
            m.update_running_info()

    @flx.action
    def set_module_content(self):
        for m in self.modules.values():
            m.set_content()

    @flx.action
    def save(self, filename):
        path = "save/%s" % filename
        last_m = None
        for m in self.modules.values():
            meta = m.retico_module.meta_data
            meta["widget"] = str(m.__class__.__name__)
            meta["left"] = m.gui.p_left
            meta["top"] = m.gui.p_top
            meta["width"] = m.gui.p_width
            meta["height"] = m.gui.p_height
            meta["active"] = m.gui.active
            meta["id"] = id(m)
            last_m = m
        headless.save(last_m.retico_module, path)
        filenames = glob.glob("save/*.rtc")
        self.widget.update_file_tree(filenames)

    @flx.action
    def load(self, filename):
        path = "save/%s" % filename
        m_list, c_list = headless.load(path)
        self.load_map = {}
        self.load_c_list = c_list
        for m in m_list:
            type = m.meta_data.get("widget", None)
            if not type:
                type = str(m.__class__.__name__)
            parent = self.get_parent(type)
            x = m.meta_data.get("left", 20)
            y = m.meta_data.get("top", 20)
            h = m.meta_data.get("height", 150)
            w = m.meta_data.get("width", 150)
            mid = m.meta_data.get("id", id(m))
            active = m.meta_data.get("active", True)
            self.load_map[mid] = m
            self.widget.create_existing_module(type, parent, x, y, w, h, mid, active)
        self.widget.load_connections()

    @flx.action
    def load_connections(self):
        for (a, b) in self.load_c_list:
            aid = a.meta_data.get("id", id(a))
            bid = b.meta_data.get("id", id(b))
            agui = self.load_map[aid]
            bgui = self.load_map[bid]
            self.widget.add_connection(agui, bgui)

    def get_parent(self, name):
        for k in modlist.MODULE_LIST.keys():
            for n in modlist.MODULE_LIST[k].keys():
                if n == name:
                    return k

    @flx.action
    def register_existing_module(self, type, parent, gui, mid):
        m = self.load_map[mid]
        self.load_map[mid] = gui
        pymodule = modlist.MODULE_LIST[parent][type](
            gui, None, m, flx_session=self.session
        )
        self.modules[id(gui)] = pymodule
        gui.set_mtitle(pymodule.retico_module.name())
        pymodule.enable_buttons()

    @flx.action
    def clear(self):
        for m in list(self.modules.values()):
            self.delete_module(m.gui)
        self.modules = {}

    @flx.action
    def toggle_module(self, gui):
        gui.set_active(not gui.active)
        gui.display_active()

    @flx.action
    def handle_trigger(self, gui, text):
        self.modules[id(gui)].handle_trigger(text)


class ReticoWidget(flx.Widget):
    def init(self, model, module_list, file_list):
        self.model = model
        self.connection_list = []
        self.running = False
        with flx.HSplit():
            with flx.Widget(flex=3):
                self.mpane = ModulePane(self)
            with flx.Widget(flex=1):
                self.menu = MenuPane(
                    self, self.mpane, module_list, file_list, style="height:100%;"
                )

    def clear(self):
        self.connection_list = []
        self.model.clear()

    @flx.action
    def update_file_tree(self, files):
        self.menu.update_file_tree(files)

    @flx.action
    def load_connections(self):
        window.setTimeout(self.model.load_connections, 10)

    def update_periodically(self):
        if self.running:
            self.model.update_module_info()
            window.setTimeout(self.update_periodically, 1000)
        else:
            self.model.set_module_content()

    def run(self):
        self.model.run()
        self.running = True
        self.update_periodically()

    def stop(self):
        self.model.stop()
        self.running = False

    @flx.action
    def set_running(self, active):
        self.mpane.set_running(active)
        if active == "red":
            self.menu.stop_button.set_disabled(False)

    @flx.action
    def create_dialogue(self, parameters, module, parent):
        ParameterBox(parameters, self.mpane, module, parent, parent=self)

    @flx.action
    def add_connection(self, from_gui, to_gui):
        if (from_gui, to_gui) in self.connection_list:
            return
        self.connection_list.append((from_gui, to_gui))
        self.draw_strokes()

    @flx.action
    def delete_module(self, gui):
        new_clist = []
        for (f, t) in self.connection_list:
            if f != gui and t != gui:
                new_clist.append((f, t))
        self.connection_list = new_clist
        self.draw_strokes()

    @flx.action
    def create_existing_module(self, type, parent, x, y, w, h, id, active):
        self.mpane.create_existing_module(type, parent, x, y, w, h, id, active)

    def draw_strokes(self):
        canvas = self.mpane.canvas.node.getContext("2d")
        canvas.clearRect(
            0, 0, self.mpane.canvas.node.width, self.mpane.canvas.node.height
        )
        for (f, t) in self.connection_list:
            f_rect = f.node.getBoundingClientRect()
            t_rect = t.node.getBoundingClientRect()
            mpanenode = self.mpane.node

            f_rect_right = f_rect.right + mpanenode.scrollLeft
            f_rect_left = f_rect.left + mpanenode.scrollLeft
            f_rect_top = f_rect.top + mpanenode.scrollTop
            f_rect_bottom = f_rect.bottom + mpanenode.scrollTop

            t_rect_left = t_rect.left + mpanenode.scrollLeft
            t_rect_right = t_rect.right + mpanenode.scrollLeft
            t_rect_bottom = t_rect.bottom + mpanenode.scrollTop
            t_rect_top = t_rect.top + mpanenode.scrollTop

            from_x, from_y = f.in_pos()
            if f_rect_right < t_rect_left - 40:
                from_x = f_rect_right
            else:
                from_x = f_rect_left
            to_x, to_y = t.out_pos()
            if t_rect_left < f_rect_right + 40:
                to_x = t_rect_right
                to_arrow_direction = +1
            else:
                to_x = t_rect_left
                to_arrow_direction = -1
            half_x = from_x + ((to_x - from_x) / 2)
            if t_rect_top > f_rect_top:
                half_y = t_rect_top + ((f_rect_bottom - t_rect_top) / 2)
            else:
                half_y = f_rect_top + ((t_rect_bottom - f_rect_top) / 2)
            canvas.beginPath()
            canvas.strokeStyle = "#fff"
            canvas.lineWidth = 3
            canvas.lineCap = "round"
            if f_rect_right > t_rect_left - 40 and f_rect_left < t_rect_right + 40:
                canvas.moveTo(from_x, from_y)
                canvas.lineTo(f_rect_left - 20, from_y)
                canvas.lineTo(f_rect_left - 20, half_y)
                canvas.lineTo(t_rect_right + 20, half_y)
                canvas.lineTo(t_rect_right + 20, to_y)
                canvas.lineTo(to_x, to_y)
                canvas.lineTo(to_x + (6 * to_arrow_direction), to_y - 4)
                canvas.lineTo(to_x + (6 * to_arrow_direction), to_y + 4)
                canvas.lineTo(to_x, to_y)
            else:
                canvas.moveTo(from_x, from_y)
                canvas.lineTo(half_x, from_y)
                canvas.lineTo(half_x, to_y)
                canvas.lineTo(to_x, to_y)
                canvas.lineTo(to_x + (6 * to_arrow_direction), to_y - 4)
                canvas.lineTo(to_x + (6 * to_arrow_direction), to_y + 4)
                canvas.lineTo(to_x, to_y)
            canvas.stroke()


class MenuPane(flx.Widget):
    def init(self, retico_widget, mpane, module_list, file_list):
        self.retico_widget = retico_widget
        self.mpane = mpane
        with flx.VBox(css_class="stupid-vbox") as stupid_vbox:
            stupid_vbox.set_padding("20px")
            with flx.TreeWidget(
                max_selected=1, style="height: 300px;", flex=1
            ) as self.module_tree:
                for k in module_list.keys():
                    with flx.TreeItem(text=k, checked=None):
                        for m in module_list[k]:
                            flx.TreeItem(text=m, checked=None)
            self.add_module_button = flx.Button(text="Add Module")
            flx.Widget(style="min-height:50px;")
            self.run_button = flx.Button(text="Run", css_class="menu-button")
            self.stop_button = flx.Button(text="Stop", css_class="menu-button")
            self.stop_button.set_disabled(True)
            flx.Widget(style="min-height:50px;")
            self.file_tree = flx.TreeWidget(
                max_selected=1, style="height:300px;", flex=1
            )
            self.update_file_tree(file_list)
            self.load_button = flx.Button(text="Load")
            self.filename_edit = flx.LineEdit()
            self.save_button = flx.Button(text="Save")
            self.clear_button = flx.Button(text="Clear")
            flx.Widget(flex=1)

    @flx.action
    def update_file_tree(self, files):
        files.sort()
        for child in self.file_tree.children:
            child.set_parent(None)
            child.dispose()
        for g in files:
            flx.TreeItem(text=g[5:], checked=None, parent=self.file_tree)

    @flx.reaction("add_module_button.pointer_click")
    def module_click(self, *events):
        if not self.module_tree.highlight_get().parent.text:
            return
        parent = self.module_tree.highlight_get().parent.text
        module = self.module_tree.highlight_get().text
        self.retico_widget.model.create_parameter_dialogue(module, parent)
        # ParameterBox(self.mpane, module, parent, parent=self.retico_widget)

    @flx.reaction("save_button.pointer_click")
    def save_click(self):
        self.retico_widget.model.save(self.filename_edit.text)

    @flx.reaction("load_button.pointer_click")
    def load_click(self):
        self.retico_widget.model.load(self.file_tree.highlight_get().text)

    @flx.reaction("run_button.pointer_click")
    def run_click(self):
        self.run_button.set_disabled(True)
        self.retico_widget.run()

    @flx.reaction("stop_button.pointer_click")
    def stop_click(self):
        self.run_button.set_disabled(False)
        self.stop_button.set_disabled(True)
        self.retico_widget.stop()

    @flx.reaction("clear_button.pointer_click")
    def clear_click(self):
        self.retico_widget.clear()


class ModulePane(flx.Widget):
    def dragMoveListener(self, event):
        target = event.target

        x = float(target.getAttribute("data-x"))
        y = float(target.getAttribute("data-y"))

        if event.rect:
            target.style.width = event.rect.width + "px"
            target.style.height = event.rect.height + "px"
            x += event.deltaRect.left
            y += event.deltaRect.top
        else:
            x += event.dx
            y += event.dy

        target.style.webkitTransform = "translate(" + x + "px, " + y + "px)"
        target.style.transform = "translate(" + x + "px, " + y + "px)"

        target.setAttribute("data-x", x)
        target.setAttribute("data-y", y)

        self.retico_widget.draw_strokes()

    def set_running(self, active):
        if active == "red":
            self.node.style["background-color"] = "#822"
        elif active == "yellow":
            self.node.style["background-color"] = "#552"
        else:
            self.node.style["background-color"] = None

    def init_moving(self):
        window.interact(".flx-ReticoModule").draggable(
            {
                "onmove": self.dragMoveListener,
                "restrict": {
                    "restriction": "parent",
                    "elementRect": {"top": 0, "left": 0, "bottom": 1, "right": 1},
                },
            }
        ).resizable(
            {
                "edges": {"left": True, "right": True, "bottom": True, "top": False},
                "restrictEdges": {"outer": "parent", "endOnly": True},
                "restrictSize": {"min": {"width": 150, "height": 150}},
            }
        ).on(
            "resizemove", self.dragMoveListener
        )

    def center_view(self):
        rect = self.node.getBoundingClientRect()
        h = rect.height / 2
        w = rect.width / 2
        if h == 0 or w == 0:
            window.setTimeout(self.center_view, 10)
            return
        self.node.scrollTop = 1500 - h
        self.node.scrollLeft = 1500 - w

    def init(self, retico_widget):
        self.retico_widget = retico_widget
        with flx.PinboardLayout(
            style="height: 3000px; width: 3000px;"
        ) as self.mcontainer:
            self.canvas = flx.CanvasWidget(
                style="left: 0; top: 0; height:100%; width: 100%;"
            )
        self.modules = []
        self.init_moving()
        window.setTimeout(self.center_view, 10)

    def create_module(self, type, parent, params):
        rect = self.node.getBoundingClientRect()
        init_x = self.node.scrollLeft + (rect.width / 2) - 75
        init_y = self.node.scrollTop + (rect.height / 2) - 75
        module = ReticoModule(
            self.retico_widget,
            parent=self.mcontainer,
            style="left: %dpx; top: %dpx;" % (init_x, init_y),
        )
        self.modules.append(module)
        self.retico_widget.model.register_module(type, parent, module, params)

    def create_existing_module(self, type, parent, x, y, w, h, id, active):
        module = ReticoModule(
            self.retico_widget,
            parent=self.mcontainer,
            style="left: %dpx; top: %dpx; width: %dpx; height: %dpx;" % (x, y, w, h),
        )
        module.set_active(active)
        module.display_active()
        self.modules.append(module)
        self.retico_widget.model.register_existing_module(type, parent, module, id)


class ReticoModule(flx.Widget):

    p_left = flx.IntProp(settable=True)
    p_top = flx.IntProp(settable=True)
    p_width = flx.IntProp(settable=True)
    p_height = flx.IntProp(settable=True)

    active = flx.BoolProp(settable=True)

    def init(self, retico_widget):
        self.retico_widget = retico_widget
        self.l_title = flx.Label(text="", css_class="title-label")
        self.close_button = flx.Button(text="X", css_class="close-button")
        with flx.VBox(
            style="cursor: default; padding-bottom: 30px; padding-left: 20px; padding-right:20px; padding-top: 30px;"
        ) as self.content_box:
            self.content_box.set_padding("20px")
        self.out_button_l = flx.Button(text="◀", css_class="out-button left-button")
        self.out_button_r = flx.Button(text="▶", css_class="out-button right-button")
        self.in_button_l = flx.Button(text="▶", css_class="in-button left-button")
        self.in_button_r = flx.Button(text="◀", css_class="in-button right-button")
        self.enable_button = flx.Button(text="enabled", css_class="enable-button")
        self.trigger_edit = flx.LineEdit(self.content_box)
        self.trigger_button = flx.Button(parent=self.content_box, text="Trigger")
        self.trigger_edit.set_parent(None)
        self.trigger_button.set_parent(None)
        self.trigger_button.set_disabled(True)
        self.set_active(True)
        self.set_position()

    def set_position(self):
        rect = self.node.getBoundingClientRect()
        mpane = self.retico_widget.mpane.node

        self.set_p_left(rect.left + mpane.scrollLeft)
        self.set_p_top(rect.top + mpane.scrollTop)
        self.set_p_width(rect.width)
        self.set_p_height(rect.height)

        window.setTimeout(self.set_position, 100)

    @flx.action
    def clear_content(self):
        for child in self.content_box.children:
            child.set_parent(None)
            child.dispose()

    @flx.action
    def add_info(self, text):
        style = "font-size: 10pt; text-align: center;"
        lbl = flx.Label(style=style, parent=self.content_box)
        lbl.set_html(text)

    @flx.action
    def update_info(self, text):
        style = "font-size: 10pt; text-align: center;"
        if len(self.content_box.children) > 1:
            self.clear_content()
            flx.Label(style=style, parent=self.content_box)
        self.content_box.children[0].set_html(text)

    @flx.action
    def create_trigger(self):
        self.trigger_edit.set_parent(self.content_box)
        self.trigger_button.set_parent(self.content_box)

    @flx.reaction("trigger_button.pointer_click")
    def trigger_clicked(self):
        params_txt = self.trigger_edit.text
        print("TRIGGER CLICKED!", str(params_txt))
        self.retico_widget.model.handle_trigger(self, params_txt)

    # @flx.action
    # def set_content(self, content_list):
    #     for child in self.content_box.children:
    #         child.set_parent(None)
    #         child.dispose()
    #     for element in content_list:
    #         element.set_parent(self.content_box)

    @flx.action
    def disable_input_buttons(self):
        self.in_button_l.set_disabled(True)
        self.in_button_r.set_disabled(True)

    @flx.action
    def disable_output_buttons(self):
        self.out_button_l.set_disabled(True)
        self.out_button_r.set_disabled(True)

    @flx.action
    def enable_input_buttons(self):
        self.in_button_l.set_disabled(False)
        self.in_button_r.set_disabled(False)

    @flx.action
    def enable_output_buttons(self):
        self.out_button_l.set_disabled(False)
        self.out_button_r.set_disabled(False)

    @flx.action
    def enable_close_button(self):
        self.close_button.set_disabled(False)
        self.trigger_button.set_disabled(True)

    @flx.action
    def disable_close_button(self):
        self.close_button.set_disabled(True)
        self.trigger_button.set_disabled(False)

    @flx.action
    def highlight(self, active, color="#ffd"):
        self.node.style["box-shadow"] = None
        if active:
            if color == "border":
                self.node.style["box-shadow"] = "rgba(255, 255, 255, 0.6) 0px 0px 20px"
            elif color == "red-border":
                self.node.style["box-shadow"] = "rgba(255, 0, 0, 0.6) 0px 0px 20px"
            else:
                self.node.style["background-color"] = color
        else:
            self.node.style["background-color"] = "#fff"

    @flx.reaction("out_button_l.pointer_click", "out_button_r.pointer_click")
    def out_button_click(self):
        if not self.retico_widget.model.connecting_state:
            self.retico_widget.model.init_out_click(self)
        else:
            self.retico_widget.model.connect_to(self)

    @flx.reaction("in_button_l.pointer_click", "in_button_r.pointer_click")
    def in_button_click(self):
        if not self.retico_widget.model.connecting_state:
            self.retico_widget.model.init_in_click(self)
        else:
            self.retico_widget.model.connect_to(self)

    @flx.reaction("close_button.pointer_click")
    def _close(self):
        self.retico_widget.model.delete_module(self)

    @flx.reaction("enable_button.pointer_click")
    def enable_button_click(self):
        self.retico_widget.model.toggle_module(self)

    @flx.action
    def set_mtitle(self, thing):
        self.l_title.set_text(thing)

    def in_pos(self):
        rect = self.node.getBoundingClientRect()
        mp_node = self.retico_widget.mpane.node
        return (
            rect.left + (rect.width / 2) + mp_node.scrollLeft,
            rect.bottom - 13 + mp_node.scrollTop,
        )

    def out_pos(self):
        rect = self.node.getBoundingClientRect()
        mp_node = self.retico_widget.mpane.node
        return (
            rect.left + (rect.width / 2) + mp_node.scrollLeft,
            rect.top + 45 + mp_node.scrollTop,
        )

    @flx.action
    def setup(self):
        self.disable_input_buttons()
        self.disable_output_buttons()
        self.disable_close_button()
        self.highlight(True, "red-border")

    @flx.action
    def stop(self):
        self.enable_close_button()
        self.highlight(False)

    @flx.action
    def display_active(self):
        if self.active:
            self.node.style["opacity"] = 1
            self.enable_button.set_text("enabled")
        else:
            self.node.style["opacity"] = 0.1
            self.enable_button.set_text("disabled")


class ParameterBox(flx.Widget):
    def init(self, parameters, mpane, module_type, mod_parent):
        flx.Label(text="Parameters for this module:", style="color: #fff;")
        self.params = flx.LineEdit(text=parameters, style="width: 500px;")
        self.okbtn = flx.Button(text="OK")
        self.mpane = mpane
        self.module_type = module_type
        self.mod_parent = mod_parent

    @flx.reaction("okbtn.pointer_click")
    def ok_click(self):
        self.set_parent(None)
        self.dispose()
        self.mpane.create_module(self.module_type, self.mod_parent, self.params.text)


def main():
    resourceserver.run_server()
    a = flx.App(ReticoBuilder)
    a.launch(runtime="chrome-browser", title="ReTiCo Builder")
    flx.run()  # Or .run() if the App should terminate after closing.
    resourceserver.stop_server()


if __name__ == "__main__":
    main()
