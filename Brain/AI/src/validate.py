import argparse
import os
from AI.src.ball_sort.helper import ball_sort,check_if_to_revalidate
from AI.src.candy_crush.helper import candy_crush, check_CCS
from AI.src.g2048.helper import g2048
from AI.src.webservices.helpers import getScreenshot
from AI.src.constants import SCREENSHOT_PATH, SCREENSHOT_FILENAME, RESOURCES_PATH, VALIDATION_PATH
import constants
import sys
from contextlib import redirect_stdout
gameDictionary = { "ball_sort" : ball_sort, "candy_crush" : candy_crush, "2048" : g2048  }
validationDictionary = { "ball_sort" : check_if_to_revalidate , "candy_crush" : check_CCS}


TRIGGER = "validate"

def add_arguments(parser):
    parser.add_argument("-g", "--games", type=str, help=f"Available games are:{gameDictionary.keys()}", choices = gameDictionary.keys(), required=True)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-T", "--tune", action="store_true", help="when enabled, the validation process will be repeated until optimum value is reached in order to tune vision parameters")
    group.add_argument("-b", "--benchmark", action="store_true", help="Benchmark mode")

def add_distinctive_argument(parser,required=False):
    
    parser.add_argument("-v", "--validate", type=str, required=required, help="screenshots to perform validation on all screenshots starting with the given prefix")

def execute(args):
    if args.benchmark:
        print("Benchmark mode")
        Start(constants.SCREENSHOT_FILENAME,args)
    validate_game(args)

def Start(screenshot,args,iteration=0):
    vision=os.path.join(VALIDATION_PATH,args.games,"vision",screenshot+".txt")
    abstraction=os.path.join(VALIDATION_PATH,args.games,"abstraction",screenshot+".txt")
    benchmark = True if args.benchmark else False
    return gameDictionary[args.games](screenshot,args.debugVision,vision,abstraction,iteration, benchmark)


def validate_game(args):
    not_done=True
    it=0
    validation_info = None 
    while(not_done):
        outputs=[]
        for filename in os.listdir(constants.SCREENSHOT_PATH):
            if filename.startswith(args.test):
                screenshot = filename
                print(f"{screenshot}")
                outputs.append(Start(screenshot,args,it))
        not_done,validation_info=validationDictionary[args.games](outputs,validation_info)
        if not args.tune:
            return
        it+=1

if __name__ == '__main__':
    msg = "This script is meant to perform validation and benchmark tasks."
    
    parser = argparse.ArgumentParser(description=msg)
    add_distinctive_argument(parser,True)
    add_arguments(parser)
    
    
    args = parser.parse_args()

    execute(args)
        

    
    

        