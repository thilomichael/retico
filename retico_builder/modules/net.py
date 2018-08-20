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

except ImportError:
    pass
