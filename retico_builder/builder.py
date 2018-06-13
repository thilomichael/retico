"""The module for the gui of the retico builder."""

from flexx import flx

from pscript import RawJS

from retico_builder import modlist

import json

flx.assets.associate_asset(__name__, "http://code.interactjs.io/v1.3.4/interact.js")

class ReticoBuilder(flx.PyComponent):

    connecting_state = flx.BoolProp(settable=True)

    def init(self):
        module_list = modlist.get_module_list()
        self.widget = ReticoWidget(self, module_list)
        self.modules = {}
        self.set_connecting_state(False)
        self.connecting_module = None
        self.connecting_direction = None

    @flx.action
    def register_module(self, type, parent, gui, params):
        pymodule = modlist.MODULE_LIST[parent][type](gui, params, flx_session=self.session)
        self.modules[id(gui)] = pymodule
        gui.set_mtitle(pymodule.retico_module.name())
        pymodule.enable_buttons()

    @flx.action
    def create_parameter_dialogue(self, type, parent):
        self.widget.create_dialogue(json.dumps(modlist.MODULE_LIST[parent][type].PARAMETERS), type, parent)

    @flx.action
    def init_out_click(self, gui):
        module = self.modules[id(gui)]
        out_iu = module.MODULE.output_iu()

        self.set_connecting_state(True)
        self.connecting_module = gui
        self.connecting_direction = 'out'

        for m in self.modules.values():
            if gui != m.gui:
                m.enable_output_iu(out_iu)

    @flx.action
    def init_in_click(self, gui):
        module = self.modules[id(gui)]
        in_ius = module.MODULE.input_ius()

        self.set_connecting_state(True)
        self.connecting_module = gui
        self.connecting_direction = 'in'

        for m in self.modules.values():
            if gui != m.gui:
                m.enable_input_ius(in_ius)

    @flx.action
    def connect_to(self, gui):

        if gui != self.connecting_module:
            if self.connecting_direction == 'in':
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
        pymod = self.modules[id(gui)]
        del self.modules[id(gui)]
        # TODO: actually remove the underlying module...

    @flx.action
    def run(self):
        for m in self.modules.values():
            m.retico_module.setup()

        for m in self.modules.values():
            print("Running", m.retico_module)
            m.retico_module.run(run_setup=False)

    @flx.action
    def stop(self):
        for m in self.modules.values():
            m.retico_module.stop()


class ReticoWidget(flx.Widget):

    CSS="""
    .flx-ReticoBuilder {
        font-family: 'Roboto', sans-serif;
    }
    """

    def init(self, model, module_list):
        self.model = model
        self.connection_list = []
        with flx.HSplit():
            self.mpane = ModulePane(self, flex=3)
            self.menu = MenuPane(self, self.mpane, module_list, flex=1)

    def run(self):
        self.mpane.set_running(True)
        self.model.run()

    def stop(self):
        self.mpane.set_running(False)
        self.model.stop()

    @flx.action
    def create_dialogue(self, parameters, module, parent):
        ParameterBox(parameters, self.mpane, module, parent, parent=self)

    @flx.action
    def add_connection(self, from_gui, to_gui):
        self.connection_list.append((from_gui, to_gui))
        self.draw_strokes()

    def delete_module(self, gui):
        new_clist = []
        for (f, t) in self.connection_list:
            if f != gui and t != gui:
                new_clist.append((f, t))
        self.connection_list = new_clist
        self.model.delete_module(gui)
        self.draw_strokes()

    def draw_strokes(self):
        canvas = self.mpane.canvas.node.getContext("2d")
        canvas.clearRect(0, 0, self.mpane.canvas.node.width, self.mpane.canvas.node.height)
        for (f, t) in self.connection_list:
            f_rect = f.node.getBoundingClientRect()
            t_rect = t.node.getBoundingClientRect()
            mpanenode = self.mpane.node

            f_rect_right = f_rect.right + mpanenode.scrollLeft
            f_rect_left = f_rect.left + mpanenode.scrollLeft
            f_rect_top = f_rect.top + mpanenode.scrollTop

            t_rect_left = t_rect.left + mpanenode.scrollLeft
            t_rect_right = t_rect.right + mpanenode.scrollLeft
            t_rect_bottom = t_rect.bottom + mpanenode.scrollTop

            from_x, from_y = f.in_pos()
            if f_rect_right < t_rect_left-40:
                from_x = f_rect_right
            else:
                from_x = f_rect_left
            to_x, to_y = t.out_pos()
            if t_rect_left < f_rect_right+40:
                to_x = t_rect_right
                to_arrow_direction = +1
            else:
                to_x = t_rect_left
                to_arrow_direction = -1
            half_x = from_x + ((to_x - from_x) / 2)
            half_y = f_rect_top + ((t_rect_bottom - f_rect_top)/2)
            canvas.beginPath()
            canvas.strokeStyle = '#fff'
            canvas.lineWidth = 3
            canvas.lineCap = 'round'
            if f_rect_right > t_rect_left-40 and f_rect_left < t_rect_right+40:
                canvas.moveTo(from_x, from_y)
                canvas.lineTo(f_rect_left-20, from_y)
                canvas.lineTo(f_rect_left-20, half_y)
                canvas.lineTo(t_rect_right+20, half_y)
                canvas.lineTo(t_rect_right+20, to_y)
                canvas.lineTo(to_x, to_y)
                canvas.lineTo(to_x+(7*to_arrow_direction), to_y-5)
                canvas.lineTo(to_x+(7*to_arrow_direction), to_y+5)
                canvas.lineTo(to_x, to_y)
            else:
                canvas.moveTo(from_x, from_y)
                canvas.lineTo(half_x, from_y)
                canvas.lineTo(half_x, to_y)
                canvas.lineTo(to_x, to_y)
                canvas.lineTo(to_x+(7*to_arrow_direction), to_y-5)
                canvas.lineTo(to_x+(7*to_arrow_direction), to_y+5)
                canvas.lineTo(to_x, to_y)
            canvas.stroke()



class MenuPane(flx.Widget):

    CSS = """
    .flx-MenuPane {
        width: 300px;
        background-color: #efefef;
        padding:20px;
    }
    .flx-split-sep {
        box-shadow: rgba(0, 0, 0, 0.5) -5px 0px 20px;
    }
    .stupid-vbox {
        padding-right: 40px;
    }
    .menu-button:disabled {
        color:#aaa;
    }
    """

    def init(self, retico_widget, mpane, module_list):
        self.retico_widget = retico_widget
        self.mpane = mpane
        with flx.VBox(css_class="stupid-vbox") as stupid_vbox:
            stupid_vbox.set_padding("20px")
            with flx.TreeWidget(max_selected=1, style="height: 300px;", flex=1) as self.module_tree:
                for k in module_list.keys():
                    with flx.TreeItem(text=k, checked=None):
                        for m in module_list[k]:
                            flx.TreeItem(text=m, checked=None)
            self.add_module_button = flx.Button(text="Add Module")
            flx.Widget(style="min-height:50px;")
            self.run_button = flx.Button(text="Run", css_class="menu-button")
            self.stop_button = flx.Button(text="Stop", css_class="menu-button")
            self.stop_button.set_disabled(True)
            flx.Widget(flex=1)

    @flx.reaction("add_module_button.pointer_click")
    def module_click(self, *events):
        if not self.module_tree.highlight_get().parent.text:
            return
        parent = self.module_tree.highlight_get().parent.text
        module = self.module_tree.highlight_get().text
        self.retico_widget.model.create_parameter_dialogue(module, parent)
        # ParameterBox(self.mpane, module, parent, parent=self.retico_widget)

    @flx.reaction("run_button.pointer_click")
    def run_click(self):
        self.run_button.set_disabled(True)
        self.stop_button.set_disabled(False)
        self.retico_widget.run()

    @flx.reaction("stop_button.pointer_click")
    def stop_click(self):
        self.run_button.set_disabled(False)
        self.stop_button.set_disabled(True)
        self.retico_widget.stop()


class ModulePane(flx.PinboardLayout):

    CSS = """
    .flx-ModulePane {
        background: #222;
        background-image: url(data:image/png;base64,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);
        width: 100%;
        height: 100%;
        overflow: scroll;
    }
    .running {
        background-color: #822;
    }
    """

    def dragMoveListener(self, event):
        target = event.target

        x = float(target.getAttribute('data-x'))
        y = float(target.getAttribute('data-y'))

        if event.rect:
            target.style.width  = event.rect.width + 'px';
            target.style.height = event.rect.height + 'px';
            x += event.deltaRect.left;
            y += event.deltaRect.top;
        else:
            x += event.dx
            y += event.dy

        target.style.webkitTransform = 'translate(' + x + 'px, ' + y + 'px)'
        target.style.transform = 'translate(' + x + 'px, ' + y + 'px)'

        target.setAttribute('data-x', x)
        target.setAttribute('data-y', y)

        self.retico_widget.draw_strokes()

    def set_running(self, active):
        if active:
            self.set_css_class(self.css_class + " running")
        else:
            self.set_css_class(self.css_class.replace(" running", ""))

    def init_moving(self):
        RawJS("interact")(".flx-ReticoModule").draggable({
            "onmove": self.dragMoveListener,
            "restrict": {"restriction": 'parent', "elementRect":
                {"top": 0, "left": 0, "bottom": 1, "right": 1 }},
        }).resizable({
            "edges": { "left": True, "right": True, "bottom": True, "top": False },
            "restrictEdges": {"outer": 'parent', "endOnly": True },
            "restrictSize": {"min": {"width": 150, "height": 150 }}
        }).on('resizemove', self.dragMoveListener)

    def init(self, retico_widget):
        self.retico_widget = retico_widget
        with flx.PinboardLayout(style="height: 3000px; width: 3000px;") as self.mcontainer:
            self.canvas = flx.CanvasWidget(style="left: 0; top: 0; height:100%; width: 100%;")
        self.modules = []
        self.init_moving()

    def create_module(self, type, parent, params):
        init_x = self.node.scrollLeft + (self.node.getBoundingClientRect().width/2) - 75
        init_y = self.node.scrollTop + (self.node.getBoundingClientRect().height/2) - 75
        module = ReticoModule(self.retico_widget, parent=self.mcontainer, style="left: %dpx; top: %dpx;" % (init_x, init_y))
        self.modules.append(module)
        self.retico_widget.model.register_module(type, parent, module, params)

class ReticoModule(flx.Widget):

    CSS = """
    .flx-ReticoModule {
        background: #fff;
        border-style: solid;
        border-width: 1px;
        border-color: #333;
        width: 150px;
        height: 150px;
        box-sizing: border-box;
        border-radius: 5px;
        box-shadow: rgba(0, 0, 0, 0.3) 3px 3px 10px;
    }
    .highlight {
        background-color: #ffd;
    }
    .title-label {
        top:0px;
        left: 0px;
        width: 100%;
        background: linear-gradient(to bottom, #ffb76b 0%,#ffa73d 50%,#ff7c00 51%,#ff7f04 100%);
        color: #333;
        font-size: 12pt;
        text-align: center;
        padding-top: 7px;
        height: 30px;
        box-shadow: rgba(0, 0, 0, 0.2) 0px 3px 2px;
        user-select: none;
    }
    .close-button {
        top: -2px;
        left: 100%;
        margin-left: -24px;
        position: absolute;
        background-color: rgba(0, 0, 0, 0);
        color: #444;
        font-weight: 100;
        margin-top: 4px;
        height: 22px;
        border-width: 0px;
        padding-top: 5px;
    }
    .close-button:hover {
        background-color: #dc3545;
        color: #fff;
    }
    .in-button {
        top: 30px;
        position: absolute;
        background-color: rgba(0,0,0,0);
        border-width: 0px;
        color: #999;
    }
    .in-button:hover {
        background-color: #28a745;
        color: #fff;
    }
    .in-button:disabled {
        color: #eee;
    }
    .in-button:disabled:hover {
        background-color: #fff;
    }
    .out-button {
        top: 100%;
        position: absolute;
        margin-top: -25px;
        background-color: rgba(0,0,0,0);
        border-width: 0px;
        display: inline-block;
        width: 30px;
        height: 28px;
        color: #999;
    }
    .out-button:hover {
        background-color: #dc3545;
        color: #fff;
    }
    .out-button:disabled {
        color: #eee;
    }
    .out-button:disabled:hover {
        background-color: #fff;
    }
    .left-button {
        left: -6px;
    }
    .right-button {
        left: 100%;
        margin-left: -24px;
    }
    """

    def init(self, retico_widget):
        self.retico_widget = retico_widget
        self.l_title = flx.Label(text="", css_class="title-label")
        self.close_button = flx.Button(text="X", css_class="close-button")
        with flx.VBox(style="cursor: default; padding-bottom: 30px; padding-left: 20px; padding-right:20px;") as self.content_box:
            self.content_box.set_padding("20px")
        self.out_button_l = flx.Button(text="◀", css_class="out-button left-button")
        self.out_button_r = flx.Button(text="▶", css_class="out-button right-button")
        self.in_button_l = flx.Button(text="▶", css_class="in-button left-button")
        self.in_button_r = flx.Button(text="◀", css_class="in-button right-button")

    @flx.action
    def set_content(self, content_list):
        for element in content_list:
            element.set_parent(self.content_box)

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
    def highlight(self, active):
        c_list = self.css_class.split(" ")
        if active:
            if "highlight" not in c_list:
                c_list.append("highlight")
        else:
            c_list = [a for a in c_list if a != "highlight"]
        self.set_css_class(" ".join(c_list))

    @flx.reaction('out_button_l.pointer_click', 'out_button_r.pointer_click')
    def out_button_click(self):
        if not self.retico_widget.model.connecting_state:
            self.retico_widget.model.init_out_click(self)
        else:
            self.retico_widget.model.connect_to(self)

    @flx.reaction('in_button_l.pointer_click', 'in_button_r.pointer_click')
    def in_button_click(self):
        if not self.retico_widget.model.connecting_state:
            self.retico_widget.model.init_in_click(self)
        else:
            self.retico_widget.model.connect_to(self)

    @flx.reaction('close_button.pointer_click')
    def _close(self):
        self.retico_widget.delete_module(self)
        self.set_parent(None)
        self.dispose()

    @flx.action
    def set_mtitle(self, thing):
        self.l_title.set_text(thing)

    def in_pos(self):
        rect = self.node.getBoundingClientRect()
        return(rect.left+(rect.width/2)+self.retico_widget.mpane.node.scrollLeft, rect.bottom-13+self.retico_widget.mpane.node.scrollTop)

    def out_pos(self):
        rect = self.node.getBoundingClientRect()
        return(rect.left+(rect.width/2)+self.retico_widget.mpane.node.scrollLeft, rect.top+45+self.retico_widget.mpane.node.scrollTop)

class ParameterBox(flx.Widget):

    CSS = """
    .flx-ParameterBox {
        background: rgba(0, 0, 0, 0.7);
        position: absolute;
        text
        left: 0;
        top: 0;
        height: 100%;
        width: 100%;
        text-align: center;
        padding-top: 20%;
    }
    """

    def init(self, parameters, mpane, type, mod_parent):
        flx.Label(text="Parameters for this module:", style="color: #fff;")
        self.params = flx.LineEdit(text=parameters, style="width: 500px;")
        self.okbtn = flx.Button(text="OK")
        self.mpane = mpane
        self.type = type
        self.mod_parent = mod_parent

    @flx.reaction('okbtn.pointer_click')
    def ok(self):
        self.set_parent(None)
        self.dispose()
        self.mpane.create_module(self.type, self.mod_parent, self.params.text)


if __name__ == '__main__':
    # m = flx.launch(ReticoBuilder)
    flx.App(ReticoBuilder).serve()
    flx.start()
    # flx.run()
