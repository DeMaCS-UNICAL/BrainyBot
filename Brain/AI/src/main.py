import argparse
import os
from AI.src.ball_sort.helper import ball_sort
from AI.src.candy_crush.helper import candy_crush
from AI.src.webservices.helpers import getScreenshot
from AI.src.constants import SCREENSHOT_PATH, SCREENSHOT_FILENAME
import constants
import sys

gameDictionary = { "ball_sort" : ball_sort, "candy_crush" : candy_crush }

def Start(screenshot,args):
    print(f"Starting AI for game {args.games}")
    gameDictionary[args.games](screenshot,args.debugVision,args.validate)

if __name__ == '__main__':
    msg = "Description"
    
    parser = argparse.ArgumentParser(description=msg)
    parser.add_argument("-g", "--games", type=str, help="Name of the games", choices = gameDictionary.keys(), required=True)
    parser.add_argument("-dV", "--debugVision", action="store_true", help="Debug screenshot")
    parser.add_argument("-t", "--test", type=str, help="screenshots to test prefix")
    parser.add_argument("-s", "--screenshot", type=str, help=f"specific screenshot filename (looks up in {constants.SCREENSHOT_PATH}))")
    parser.add_argument("-v", "--validate", type=str, help=f"Validate vision and abstraction using the specific ASP program (looks up in {constants.RESOURCES_PATH})")
    
    args = parser.parse_args()
    
    
    #game = parser.parse_args()
    #print (f"Taking first screenshot from {constants.SCREENSHOT_SERVER_IP}...")
    # TODO: change ip!

    if args.test == None:
        screenshot = constants.SCREENSHOT_FILENAME
        if not args.debugVision:
            server_ip, port = constants.SCREENSHOT_SERVER_IP, 5432
            try:
                if getScreenshot(server_ip, port):
                    print("SCREENSHOT TAKEN.")
                else:
                    exit(1)
            except Exception as e:
                print(e)
                exit(1)
        else:
            screenshot=""
            if args.screenshot == None:
                screenshot = args.games+"Test.jpg"
            else:
                screenshot = args.screenshot
            print("DEBUG MODE ON")   
            print(screenshot)
        Start(screenshot,args)
    else:
        if args.games == "ball_sort":
            print("Screenshot\t#FullTubes\t#EmptyTubes\t#Balls\t#Colors", file=sys.stderr)
        for filename in os.listdir(constants.SCREENSHOT_PATH):
            if filename.startswith(args.test):
                screenshot = filename
                print(f"{screenshot}")
                print(f"{screenshot.split('.')[1]}\t",end='',file=sys.stderr)
                Start(screenshot,args)
    
    

        