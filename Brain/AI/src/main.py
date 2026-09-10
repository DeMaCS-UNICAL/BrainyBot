import argparse
import os
from AI.src.ball_sort.helper import ball_sort, check_if_to_revalidate
#from AI.src.candy_crush.clean_helper import candy_crush
from AI.src.candy_crush.helper import check_CCS
from AI.src.g2048.helper import g2048
from AI.src.monogram.helper import monogram  # NEW: Import monogram helper
from AI.src.webservices.helpers import getScreenshot
from AI.src.constants import SCREENSHOT_PATH, SCREENSHOT_FILENAME, RESOURCES_PATH, VALIDATION_PATH
import constants
import sys
from contextlib import redirect_stdout

# Dictionary mapping game names to their solver functions
gameDictionary = { 
    "ball_sort": ball_sort, 
    #"candy_crush": candy_crush, 
    "2048": g2048,
    "monogram": monogram  # NEW: Add monogram to game dictionary
}

# Dictionary mapping games that support validation
validationDictionary = { 
    "ball_sort": check_if_to_revalidate, 
    #"candy_crush": check_CCS
    # Add monogram validation function here if you implement one
}


def Start(screenshot, args, iteration=0):
    """
    Start the solver for the specified game.
    
    Args:
        screenshot: Filename of the screenshot
        args: Command line arguments
        iteration: Current iteration (for validation)
    
    Returns:
        Result from the game solver
    """
    validate = None
    vision = None
    abstraction = None
    
    # Setup validation files if test mode is enabled
    if args.test != None:
        vision = os.path.join(VALIDATION_PATH, args.games, "vision", screenshot + ".txt")
        abstraction = os.path.join(VALIDATION_PATH, args.games, "abstraction", screenshot + ".txt")
    
    benchmark = True if args.benchmark else False
    
    # Call the appropriate game solver
    return gameDictionary[args.games](
        screenshot, 
        args.debugVision, 
        vision, 
        abstraction, 
        iteration, 
        benchmark
    )


def validate_game(args):
    """
    Validate game solver against test screenshots.
    
    Args:
        args: Command line arguments (must contain --test prefix)
    """
    not_done = True
    last_distance = 10000
    previous_threshold = 0
    it = 0
    validation_info = None 
    
    while(not_done):
        outputs = []
        info = []
        
        # Find all screenshots matching the test prefix
        for filename in os.listdir(constants.SCREENSHOT_PATH):
            if filename.startswith(args.test):
                screenshot = filename
                print(f"Testing: {screenshot}")
                
                # Run solver on test screenshot
                with open(os.path.join(VALIDATION_PATH, args.games, "vision", screenshot + '.txt'), 'w') as f:
                    with redirect_stdout(f):
                        outputs.append(Start(screenshot, args, it))
        
        # Optional: Use validation function if available
        if args.games in validationDictionary:
            not_done, validation_info = validationDictionary[args.games](outputs, validation_info)
        else:
            not_done = False
        
        it += 1


if __name__ == '__main__':
    import multiprocessing
    multiprocessing.set_start_method('spawn', force=True)

    msg = "BrainyBot Game Solver - Automated puzzle game solver using vision and ASP logic"
    
    parser = argparse.ArgumentParser(description=msg)
    
    # Game selection
    parser.add_argument(
        "-g", "--games", 
        type=str, 
        help="Name of the game to solve", 
        choices=gameDictionary.keys(), 
        required=True
    )
    
    # Debug options
    parser.add_argument(
        "-dV", "--debugVision", 
        action="store_true", 
        help="Enable debug mode for vision processing (displays intermediate images)"
    )
    
    # Testing mode
    parser.add_argument(
        "-t", "--test", 
        type=str, 
        help="Run validation tests: screenshots to test (prefix matching)"
    )
    
    # Screenshot selection
    parser.add_argument(
        "-s", "--screenshot", 
        type=str, 
        help=f"Specific screenshot filename to use (looks up in {constants.SCREENSHOT_PATH})"
    )
    
    # Benchmark mode
    parser.add_argument(
        "-b", "--benchmark", 
        action="store_true", 
        help="Run in benchmark mode (performance testing)"
    )
    
    args = parser.parse_args()

    # ============ EXECUTION MODES ============
    
    if args.benchmark:
        # Benchmark mode: test performance
        print(f"Running {args.games} in BENCHMARK mode")
        Start(constants.SCREENSHOT_FILENAME, args)
    
    elif args.test is None:
        # Normal mode: solve a single game
        print(f"Starting {args.games} solver...")
        
        # Determine which screenshot to use
        screenshot = constants.SCREENSHOT_FILENAME
        
        if args.screenshot is not None:
            # Use specified screenshot
            screenshot = args.screenshot
            print(f"Using screenshot: {screenshot}")
        else:
            # Take a new screenshot from server
            server_ip, port = constants.SCREENSHOT_SERVER_IP, 5432
            try:
                print(f"Connecting to screenshot server at {server_ip}:{port}...")
                if getScreenshot(server_ip, port):
                    print("✓ Screenshot captured successfully")
                else:
                    print("✗ Failed to capture screenshot")
                    exit(1)
            except Exception as e:
                print(f"✗ Error connecting to screenshot server: {e}")
                exit(1)
        
        # Start the solver
        try:
            result = Start(screenshot, args)
            if result is not None:
                print(f"Game solver completed. Result: {result}")
        except Exception as e:
            print(f"✗ Error during game solving: {e}")
            exit(1)
    
    else:
        # Validation mode: test against multiple screenshots
        print(f"Running {args.games} in VALIDATION mode")
        print(f"Testing screenshots with prefix: {args.test}")
        validate_game(args)