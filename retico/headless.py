"""A Module that allows for saving and loading networks from and to file."""

import sys
import pickle


def load(filename):
    """Loads a network from file and returns a list of modules in that network.

    The connections between the module have been set according to the file.

    Args:
        filename (str): The path to the .rtc file containing a network.

    Returns:
        (list): A list of Modules that are connected and ready to be run.
    """
    mc_list = pickle.load(open(filename, "rb"))
    module_dict = {}
    module_list = []
    for m in mc_list[0]:
        mod = m["retico_class"](**m["retico_args"])
        module_dict[m["id"]] = mod
        module_list.append(mod)
    for ida, idb in mc_list[1]:
        module_dict[idb].subscribe(module_dict[ida])

    return module_list


def load_and_execute(filename):
    """Loads a network from file and runs it.

    The network is loaded via the load-Method. Before running the network, it is
    setup.

    Args:
        filename (str): The path to the .rtc file containing a network.
    """
    module_list = load(filename)

    for module in module_list:
        module.setup()

    for module in module_list:
        module.run(run_setup=False)

    input()

    for module in module_list:
        module.stop()


def _discover_modules(module):
    discovered_lb = []
    discovered_rbs = []
    lb = module.left_buffer()
    if lb and lb.provider:
        discovered_lb.append(lb.provider)
    for rb in module.right_buffers():
        if rb and rb.consumer:
            discovered_rbs.append(rb.consumer)
    return set(discovered_lb), set(discovered_rbs)


def save(module, filename):
    """Saves a network to file given a module or a list of modules.

    The network is automatically detected by traversing all left and right
    buffers of the modules given. If the argument module is only a single
    module, the network that is being saved consists only of the module
    reachable from this module. If a network should be saved that is splitted
    into multiple parts, at least one module of each split has to be included
    into the module-list.

    Args:
        module (AbstractModule or list): A module of the network or a list of
            multiple modules of the network.
        filename (str): The path to where the network should be stored. This
            excludes the file-ending .rtc that will be automatically added by
            this function.
    """
    if not isinstance(module, list):
        module = [module]
    undiscovered = set(module)
    discovered = []
    m_list = []
    c_list = []
    while undiscovered:
        current_module = undiscovered.pop()
        discovered.append(current_module)
        lbs, rbs = _discover_modules(current_module)
        for mod in lbs:
            if mod not in discovered:
                undiscovered.add(mod)
        for mod in rbs:
            if mod not in discovered:
                undiscovered.add(mod)
        current_dict = {}
        current_dict["widget_name"] = current_module.name()
        current_dict["retico_class"] = current_module.__class__
        current_dict["args"] = None
        current_dict["x"] = None
        current_dict["y"] = None
        current_dict["id"] = id(current_module)
        m_list.append(current_dict)
        for buf in current_module.right_buffers():
            c_list.append((id(buf.consumer), id(buf.provider)))
    pickle.dump([m_list, c_list], open("%s.rtc" % filename, "wb"))


if __name__ == '__main__':
    load_and_execute(sys.argv[1])