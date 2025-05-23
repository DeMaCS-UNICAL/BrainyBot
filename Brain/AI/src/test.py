import argparse
from AI.src.ball_sort.helper import ball_sort
from AI.src.candy_crush.helper import candy_crush
from AI.src.g2048.helper import g2048
from AI.src.webservices.helpers import getScreenshot
import constants
gameDictionary = { "ball_sort" : ball_sort, "candy_crush" : candy_crush, "2048" : g2048  }

TRIGGER = "test"

def add_arguments(parser):
    parser.add_argument("-g", "--games", type=str, help=f"Available games are:{gameDictionary.keys()}", choices = gameDictionary.keys(), required=True)
    parser.add_argument("-dV", "--debugVision", action="store_true", help="Enable vision debugging ")

def add_distinctive_argument(parser,required=False):
    parser.add_argument("-t", "--test", type=str, required=required, help=f"specific screenshot filename (looks up in {constants.SCREENSHOT_PATH}))")

def execute(args):
    screenshot = args.screenshot
    Start(screenshot,args)


def Start(screenshot):
    return gameDictionary[args.games](screenshot,True)


if __name__ == '__main__':
    msg = "Description"
    
    parser = argparse.ArgumentParser(description=msg)
    add_distinctive_argument(parser,True)
    add_arguments(parser)
    args = parser.parse_args()

    execute(args)
        
    
        

    
    

        