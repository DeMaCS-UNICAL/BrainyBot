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