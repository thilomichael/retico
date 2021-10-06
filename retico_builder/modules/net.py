from flexx import flx
from retico_builder.modules.abstract import AbstractModule

try:
    from retico.modules.net import network

    class DelayedNetworkModule(AbstractModule):

        MODULE = network.DelayedNetworkModule
        PARAMETERS = {"delay": 0.5}

        def set_content(self):
            self.gui.clear_content()
            self.gui.add_info("Delay: %.2f" % self.retico_module.delay)

        def update_running_info(self):
            latest_iu = self.retico_module.latest_iu()
            if latest_iu:
                self.gui.update_info("Dum dee doo")

    class PacketLossNetworkModule(AbstractModule):

        MODULE = network.PacketLossNetworkModule
        PARAMETERS = {"ppl": 0.1, "burstr": 2.0}

        def set_content(self):
            self.gui.clear_content()
            self.gui.add_info("Ppl: %.2f" % self.retico_module.ppl)
            self.gui.add_info("Burstr: %.2f" % self.retico_module.burstr)

        def update_running_info(self):
            latest_iu = self.retico_module.latest_iu()
            if latest_iu:
                self.gui.update_info("Dum dee doo")

    class DelayPacketLossNetworkModule(AbstractModule):

        MODULE = network.DelayPacketLossNetworkModule
        PARAMETERS = {"delay": 0.5, "ppl": 0.1, "burstr": 2.0}

        def set_content(self):
            self.gui.clear_content()
            self.gui.add_info("Delay: %.2f" % self.retico_module.delay)
            self.gui.add_info("Ppl: %.2f" % self.retico_module.ppl)
            self.gui.add_info("Burstr: %.2f" % self.retico_module.burstr)

        def update_running_info(self):
            latest_iu = self.retico_module.latest_iu()
            if latest_iu:
                self.gui.update_info("Dum dee doo")


except ImportError:
    pass
