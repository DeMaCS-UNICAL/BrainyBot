import argparse
from AI.src.ball_sort.helper import ball_sort
from AI.src.candy_crush.helper import candy_crush
from AI.src.webservices.helpers import getScreenshot
from AI.src.constants import SCREENSHOT_PATH
import constants

if __name__ == '__main__':

    msg = "Description"
    
    parser = argparse.ArgumentParser(description=msg)
    parser.add_argument("-g", "--games", type=str, help="Name of the games", choices = ["ball_sort", "candy_crush"], required=True)
    parser.add_argument("-d", "--debug", action="store_true", help="Debug screenshot")
    
    args = parser.parse_args()
    #game = parser.parse_args()
    #print (f"Taking first screenshot from {constants.SCREENSHOT_SERVER_IP}...")
    # TODO: change ip!
    if not args.debug:
        server_ip, port = constants.SCREENSHOT_SERVER_IP, 5432
        try:
            getScreenshot(server_ip, port)
            print("SCREENSHOT TAKEN.")
        except Exception as e:
            print(e)
    else:
        print("DEBUG MODE ON")   # Will not take a screenshot from the phone, but will use the screenshot in the resources folder.
    if args.games == "ball_sort":
        ball_sort(args.debug)
    elif args.games == "candy_crush":
        candy_crush(args.debug)
        