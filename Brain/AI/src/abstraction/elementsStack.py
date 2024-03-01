class ElementsStacks:
    __instance = None
    __inited = False

    def Clean(self):
        ElementsStacks.__instance=None
        ElementsStacks.__inited=False


    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    def __init__(self,  tolerance=50,max_distance=150, min_number_elements=4) -> None:
        if type(self).__inited:
            return
        type(self).__inited = True
        self.__stacks = []
        self.__tolerance = tolerance
        self.__max_distance = max_distance
        self.__min_number_elements = min_number_elements
    '''
    def setup_non_empty_stack(self, elements: list):
        elements.sort(key=lambda x: x[1])
        while elements:
            element = elements.pop()  # ball object format: [ x coordinate, y coordinate, [R, G, B] ]
            stack_found = False
            for stack in self.__stacks:
                if stack.get_x() - self.__tolerance <= element[0] <= stack.get_x() + self.__tolerance:
                    stack_elements = stack.get_elements()
                    for b in stack_elements:
                        if abs(element[1] - b[1]) <= self.__max_distance:
                            stack.add_element(element)
                            stack_found = True
                            break
            if not stack_found:
                stack = Stack()
                stack.add_element(element)
                stack.set_x_coordinates(element[0])
                self.__stacks.append(stack)

        self.__stacks[:] = [stack for stack in self.__stacks if len(stack.get_elements()) >= self.__min_number_elements]
        [stack.set_y_coordinate() for stack in self.__stacks]

    def setup_empty_stack(self, coordinates: list):
        for c in coordinates:
            stack = Stack()
            stack.set_x_coordinates(c[0])
            stack.set_y_coordinate(c[1])
            self.__stacks.append(stack)

        # for tube in BallsChart.tubes:
        #    print(f"Tube x: {tube.get_x()} | Tube y: {tube.get_y()}")
        #    print(tube.get_balls())
    '''
    def add_stacks(self, elements:list):
        self.__stacks.extend(elements)
        
    def get_stacks(self):
        return self.__stacks
    
    def get_empty_stack(self)->list:
        to_return=[]
        for stack in self.__stacks:
            if len(stack.get_elements())==0:
                to_return.append(stack)
        return to_return
    