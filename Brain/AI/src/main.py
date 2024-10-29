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


def Start(screenshot,args,iteration=0):
    validate=None
    vision=None
    abstraction=None
    if args.test!=None:
        vision=os.path.join(VALIDATION_PATH,args.games,"vision",screenshot+".txt")
        abstraction=os.path.join(VALIDATION_PATH,args.games,"abstraction",screenshot+".txt")
    return gameDictionary[args.games](screenshot,args.debugVision,vision,abstraction,iteration)


def validate_game(args):
    not_done=True
    last_distance=10000
    previous_threshold = 0
    it=0
    validation_info = None 
    while(not_done):
        outputs=[]
        info=[]
        for filename in os.listdir(constants.SCREENSHOT_PATH):
            if filename.startswith(args.test):
                screenshot = filename
                print(f"{screenshot}")
                #print(f"{screenshot.split('.')[1]}\t",end='',file=sys.stderr)
                #with open(RESOURCES_PATH+"/"+screenshot+".txt",'w+') as f:
                #  print(f"{screenshot.split('.')[1]}\t",end='',file=f)
                
                #print(f"Starting AI for game {args.games}")
                #with open(os.path.join(VALIDATION_PATH,"ball_sort","vision",screenshot+'.txt'), 'w') as f:
                #    with redirect_stdout(f):
                outputs.append(Start(screenshot,args,it))
        #not_done,validation_info=validationDictionary[args.games](outputs,validation_info)
        not_done=False
        it+=1

if __name__ == '__main__':
    msg = "Description"
    
    parser = argparse.ArgumentParser(description=msg)
    parser.add_argument("-g", "--games", type=str, help="Name of the games", choices = gameDictionary.keys(), required=True)
    parser.add_argument("-dV", "--debugVision", action="store_true", help="Debug screenshot")
    parser.add_argument("-t", "--test", type=str, help="screenshots to test prefix")
    parser.add_argument("-s", "--screenshot", type=str, help=f"specific screenshot filename (looks up in {constants.SCREENSHOT_PATH}))")
    
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
        validate_game(args)
        

    
    

        