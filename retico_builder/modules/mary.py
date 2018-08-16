from flexx import flx
from retico_builder.modules.abstract import AbstractModule

try:
    from retico.modules.mary import tts

    class MaryTTSModule(AbstractModule):

        MODULE = tts.MaryTTSModule
        PARAMETERS = {"language_code": "de", "voice_name": "bits1-hsmm", "server_address": "localhost", "port": 59125}

        def set_content(self):
            self.gui.clear_content()
            self.gui.add_info("Language: %s" % self.retico_module.language_code)
            self.gui.add_info("Voice Name: %s" % self.retico_module.voice_name)

        def update_running_info(self):
            latest_iu = self.retico_module.latest_iu()
            if latest_iu:
                self.gui.update_info("<b>Produced speech:</b><br/>%s" % (latest_iu.grounded_in.get_text()))

except ImportError:
    pass
