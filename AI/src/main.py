import argparse
from AI.src.ball_sort.helper import ball_sort
from AI.src.candy_crush.helper import candy_crush
from AI.src.webservices.helpers import require_image_from_url

if __name__ == '__main__':

    msg = "Description"
    
    parser = argparse.ArgumentParser(description=msg)
    parser.add_argument("-g", "--game", type=str, help="Name of the games", choices = ["ball_sort", "candy_crush"], required=True)
    args = parser.parse_args()

    '''# TODO: change ip!
    server_ip, port = "192.168.1.33", 5432
    try:
        require_image_from_url(server_ip, port)
        print("SCREENSHOT TAKEN.")
    except Exception as e:
        print(e)'''
        
    if args.game == "ball_sort":
        ball_sort()
    elif args.game == "candy_crush":
        candy_crush()
        