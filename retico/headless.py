import sys
import pickle

def main(filename):
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


if __name__ == '__main__':
    main(sys.argv[1])
