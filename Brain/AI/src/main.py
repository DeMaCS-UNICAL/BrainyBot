import argparse
import os
import importlib

gameList = [ "ball_sort", "candy_crush", "2048"]
import constants
modules = ["play","test","validate"]
modules_import=[]

def main():
    # 1) build top-level parser, with shared flags but *no* script-specific ones
    parser = argparse.ArgumentParser(prog="main")

    group = parser.add_mutually_exclusive_group(required=True)

    for module in modules:
        modules_import.append(importlib.import_module(module))
        modules_import[-1].add_distinctive_argument(group)

    # 3) preliminary parse to know which module and to capture shared flags
    known, rest = parser.parse_known_args()
    to_invoke=None
    for mod in modules_import:
        if getattr(known,mod.TRIGGER,False):
            to_invoke=mod
            to_invoke.add_arguments(parser)
            break


    # 7) re-parse *all* args, validating both shared and module-specific flags
    args = parser.parse_args()  # this time will error if unknown or missing

    # 8) dispatch to the module’s execute()
    mod.execute(args)


if __name__ == "__main__":
    main()

    

    
    

        