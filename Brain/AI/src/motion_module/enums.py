from enum import Enum


class Direction(Enum):
    HORIZONTAL = 0
    VERTICAL = 1


class Orientation(Enum):
    DESCENDING = 0
    ASCENDING = 1


class MotionType(Enum):
    SWIPE = 0
    TAP = 1
    TIMED = 2


class Towards(Enum):
    TOP = 0
    RIGHT = 1
    BOTTOM = 2
    LEFT = 3
