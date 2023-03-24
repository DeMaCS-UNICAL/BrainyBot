class BallsChart:
    __instance = None
    __inited = False

    TOLERANCE = 50
    MAX_BALL_DISTANCE = 150

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    def __init__(self) -> None:
        if type(self).__inited:
            return
        type(self).__inited = True
        self.__tubes = []

    def setup_full_tubes(self, balls: list):
        balls.sort(key=lambda x: x[1])
        while balls:
            ball = balls.pop()  # ball object format: [ x coordinate, y coordinate, [R, G, B] ]
            tube_found = False
            for tube in self.__tubes:
                if tube.get_x() - BallsChart.TOLERANCE <= ball[0] <= tube.get_x() + BallsChart.TOLERANCE:
                    tube_balls = tube.get_balls()
                    for b in tube_balls:
                        if abs(ball[1] - b[1]) <= BallsChart.MAX_BALL_DISTANCE:
                            tube.add_ball(ball)
                            tube_found = True
                            break
            if not tube_found:
                tube = Tube()
                tube.add_ball(ball)
                tube.set_x_coordinates(ball[0])
                self.__tubes.append(tube)

        self.__tubes[:] = [tube for tube in self.__tubes if len(tube.get_balls()) >= 4]
        [tube.set_y_coordinate() for tube in self.__tubes]

    def setup_empty_tubes(self, coordinates: list):
        for c in coordinates:
            tube = Tube()
            tube.set_x_coordinates(c[0])
            tube.set_y_coordinate(c[1])
            self.__tubes.append(tube)

        # for tube in BallsChart.tubes:
        #    print(f"Tube x: {tube.get_x()} | Tube y: {tube.get_y()}")
        #    print(tube.get_balls())

    def get_tubes(self):
        return self.__tubes


class Tube:
    def __init__(self):
        self.__x = 0
        self.__y = 0
        self.__balls = []

    def get_x(self):
        return self.__x

    def get_y(self):
        return self.__y

    def get_balls(self) -> list:
        return self.__balls

    def set_x_coordinates(self, x):
        self.__x = x

    def set_y_coordinate(self, y=None):
        if y is None:
            self.__y = int(sum([ball[1] for ball in self.__balls]) / len(self.__balls))
        else:
            self.__y = y

    def sort_balls(self):
        pass

    def add_ball(self, ball: list):
        self.__balls.append(ball)
