import os

SRC_PATH = os.path.dirname(__file__)  # Where your .py file is located
RESOURCES_PATH = os.path.join(SRC_PATH, 'resources')
DLV_PATH = os.path.join(RESOURCES_PATH, 'dlv')
SPRITE_PATH = os.path.join(RESOURCES_PATH, 'sprites')

RED = "red"
BLUE = "blue"
YELLOW = "yellow"
GREEN = "green"
PURPLE = "purple"
ORANGE = "orange"
WHITE = "white"
nameColor = {
    RED: (255, 0, 0),
    BLUE: (0, 0, 255),
    YELLOW: (255, 255, 0),
    GREEN: (0, 255, 0),
    PURPLE: (128, 0, 128),
    ORANGE: (255, 165, 0),
    WHITE: (255, 255, 255)
}
