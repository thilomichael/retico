import inspect

from retico_builder.modules import audio, abstract, google, rasa, simulation, \
    mary, net, text, trigger, convsim

INSPECT_MODULES = {
    "Audio": audio,
    "Text": text,
    "Google": google,
    "Rasa": rasa,
    "Simulation": simulation,
    "Mary": mary,
    "Network": net,
    "Trigger": trigger,
    "ConvSim": convsim
}

# MODULE_LIST = {
#     "ReTiCo": {
#
#     },
#     "Google": {
#
#     },
#     "Rasa": {
#
#     }
# }
#
# MODULE_LIST["ReTiCo"]["SpeakerModule"] = SpeakerModule
# MODULE_LIST["ReTiCo"]["MicrophoneModule"] = MicrophoneModule
# MODULE_LIST["ReTiCo"]["StreamingSpeakerModule"] = StreamingSpeakerModule

def generate_module_list():
    m_list = {}
    for name, module in INSPECT_MODULES.items():
        current_dict = {}
        for n, obj in inspect.getmembers(module):
            if inspect.isclass(obj) and issubclass(obj, abstract.AbstractModule) and obj is not abstract.AbstractModule and obj is not abstract.AbstractTriggerModule:
                current_dict[n] = obj
        m_list[name] = current_dict
    return m_list


MODULE_LIST = generate_module_list()

def get_module_list():
    thing = {}
    for k in MODULE_LIST.keys():
        thing[k] = []
        for m in MODULE_LIST[k].keys():
            thing[k].append(m)
    return thing
