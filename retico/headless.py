import sys
import pickle

def load_and_execute(filename):
    """Runs a retico network by its given filename."""
    mc_list = pickle.load(open(filename, "rb"))
    module_dict = {}
    for m in mc_list[0]:
        mod = m["retico_class"](**m["retico_args"])
        module_dict[m["id"]] = mod
    for ida, idb in mc_list[1]:
        module_dict[idb].subscribe(module_dict[ida])

    for _, module in module_dict.items():
        module.run()

    input()

    for _, module in module_dict.items():
        module.stop()

def discover_all_modules(module):
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
    if not isinstance(module, list):
        module = [module]
    undiscovered = set(module)
    discovered = []
    m_list = []
    c_list = []
    while undiscovered:
        current_module = undiscovered.pop()
        discovered.append(current_module)
        lbs, rbs = discover_all_modules(current_module)
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
