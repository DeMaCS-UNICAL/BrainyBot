
from AI.src.puzzle_bubble.detect.new_detect import MatchingBubblePuzzle


def puzzle_bubble(screenshot, debug = True, validation=None):
    matcher = MatchingBubblePuzzle(screenshot,debug,validation)
    matcher.SearchGrid()