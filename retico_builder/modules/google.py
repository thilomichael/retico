from flexx import flx
from retico_builder.modules.abstract import AbstractModule

try:
    from retico.modules.google import asr, tts

    class GoogleASRModule(AbstractModule):

        MODULE = asr.GoogleASRModule
        PARAMETERS = {"language": "en-US", "nchunks": 20, "rate": 44100}

        def set_content(self):
            self.gui.clear_content()
            self.gui.add_info("Language: %s" % self.retico_module.language)
            self.gui.add_info("Number of chunks: %d" % self.retico_module.nchunks)
            self.gui.add_info("Rate: %d" % self.retico_module.rate)

        def update_running_info(self):
            latest_iu = self.retico_module.latest_iu()
            if latest_iu:
                self.gui.update_info("Recognized Speech:<br>%s<br/>(confidence: %.2f, stability: %.2f)" % (latest_iu.text, latest_iu.confidence, latest_iu.stability))

    class GoogleTTSModule(AbstractModule):

        MODULE = tts.GoogleTTSModule
        PARAMETERS = {"language_code": "en-US", "voice_name": "en-US-Wavenet-A", "speaking_rate": 1.4}

        def set_content(self):
            self.gui.clear_content()
            self.gui.add_info("Language: %s" % self.retico_module.language_code)
            self.gui.add_info("Voice Name: %s" % self.retico_module.voice_name)
            self.gui.add_info("Speaking Rate: %.2f" % self.retico_module.speaking_rate)

        def update_running_info(self):
            latest_iu = self.retico_module.latest_iu()
            if latest_iu:
                self.gui.update_info("<b>Produced speech:</b><br/>%s" % (latest_iu.grounded_in.get_text()))

except ImportError:
    pass
