
import os

SRC_PATH = os.path.dirname(__file__)  # Where your .py file is located
RESOURCES_PATH = os.path.join(SRC_PATH, 'resources')
SPRITE_PATH = os.path.join(RESOURCES_PATH, 'sprites')

#it can change based on the videogame used
GRID_START_APPROXIMATION=0.12
GRID_END_APPROXIMATION=0.67
PLAYER_BUBBLE_END_APPROXIMATION=0.83
MAX_BUBBLES_PER_ROW=11