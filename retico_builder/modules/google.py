"""A module for google module widgets."""

from retico_builder.modules.abstract import InfoLabelWidget

try:
    from retico.modules.google.asr import GoogleASRModule

    class GoogleASRModuleWidget(InfoLabelWidget):
        """A module widget providing asr by google."""

        retico_class = GoogleASRModule
        args = {"language": "en-US", "nchunks": 20}

        def update_info(self):
            iu = self.module.latest_iu()
            if iu:
                self.info_label.text = iu.get_text()

except ImportError:
    pass
