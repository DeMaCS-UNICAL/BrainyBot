from AI.src.g2048.detect.new_detect import Matching2048

def g2048(screenshot, debug = False, validation=None,iteration=0):
    matcher = Matching2048(screenshot,debug,validation,iteration)
    print(matcher.find_numbers())