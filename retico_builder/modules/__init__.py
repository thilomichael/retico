import pkgutil
import inspect

from retico_builder.modules.abstract import ModuleWidget

AVAILABLE_MODULES = {}
bad_m = ["ModuleWidget", "InfoLabelWidget"]

for importer, modname, ispkg in pkgutil.iter_modules(__path__):
    m = importer.find_module(modname).load_module(modname)
    clsmembers = inspect.getmembers(m, inspect.isclass)
    for _, clsm in clsmembers:
        if not issubclass(clsm, ModuleWidget) or clsm.name() in bad_m:
            continue
        AVAILABLE_MODULES[clsm.name()] = clsm
