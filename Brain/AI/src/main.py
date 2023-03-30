import argparse
from AI.src.ball_sort.helper import ball_sort
from AI.src.candy_crush.helper import candy_crush
from AI.src.webservices.helpers import require_image_from_url
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
    server_ip, port = constants.SCREENSHOT_SERVER_IP, 5432
    try:
        require_image_from_url(server_ip, port)
        print("SCREENSHOT TAKEN.")
    except Exception as e:
        print(e)
        
    if args.games == "ball_sort":
        ball_sort(args.debug)
    elif args.games == "candy_crush":
        candy_crush()
        