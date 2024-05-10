import os

SRC_PATH = os.path.dirname(__file__)  # Where your .py file is located
RESOURCES_PATH = os.path.join(SRC_PATH, 'resources')
SPRITE_PATH = os.path.join(RESOURCES_PATH, 'sprites')

#
# Do not compute plans longer than that in ball sort
#
MAX_STEPS = 100 # Should be in multiples of LOOK_AHEAD or MAX_STEPS % LOOK_AHEAD steps will not be planned
LOOK_AHEAD = 2  # How many steps to plan ahead in ball sort