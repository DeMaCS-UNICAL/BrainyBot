import os

SRC_PATH = os.path.dirname(__file__)
RESOURCES_PATH = os.path.join(SRC_PATH, 'resources')

OBSTACLE_GROUND, OBSTACLE_LOW, OBSTACLE_HIGH = 0, 1, 2
DISTANCE_NEAR, DISTANCE_FAR = 0, 1
ACTION_JUMP, ACTION_DUCK, ACTION_NONE = 0, 1, 2

OBSTACLE_KIND = {
    "cactus_small": OBSTACLE_GROUND,
    "cactus_large": OBSTACLE_GROUND,
    "cactus_group": OBSTACLE_GROUND,
    "pterodactyl_low": OBSTACLE_LOW,
    "pterodactyl_high": OBSTACLE_HIGH,
}

NEAR_THRESHOLD_PX = 300
DUCK_DURATION_MS = 400
