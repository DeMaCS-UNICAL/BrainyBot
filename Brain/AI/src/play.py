import argparse
from AI.src.ball_sort.helper import ball_sort
from AI.src.candy_crush.helper import candy_crush
from AI.src.g2048.helper import g2048
from AI.src.webservices.helpers import getScreenshot
import constants

gameDictionary = { "ball_sort" : ball_sort, "candy_crush" : candy_crush, "2048" : g2048  }
TRIGGER = "play"

def add_arguments(parser):
    parser.add_argument("-g", "--games", type=str, help=f"Available games are:{gameDictionary.keys()}", choices = gameDictionary.keys(), required=True)
    parser.add_argument("-dV", "--debugVision", action="store_true", help="Enable vision debugging ")
    
def add_distinctive_argument(group):
    group.add_argument("-p", "--play", action="store_true", help="Play mode ")

def execute(args):
    screenshot = constants.SCREENSHOT_FILENAME
    
    server_ip, port = constants.SCREENSHOT_SERVER_IP, 5432
    try:
        if getScreenshot(server_ip, port):
            print("SCREENSHOT TAKEN.")
        else:
            exit(1)
    except Exception as e:
        print(e)
        exit(1)
    Start(screenshot,args)

def Start(screenshot,args):
    return gameDictionary[args.games](screenshot,args.debugVision)


if __name__ == '__main__':
    msg = "Description"
    
    parser = argparse.ArgumentParser(description=msg)
    add_arguments(parser)
    args = parser.parse_args()
    execute(args)
    

    
        

    
    

        