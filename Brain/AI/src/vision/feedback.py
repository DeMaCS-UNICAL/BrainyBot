import asyncio
import cv2
import numpy as np
from languages.mapper import Mapper
from languages.predicate import Predicate
from time import sleep
class Feedback:
    feedbackers=[]
    def __init__(self, tolerance=0):
        self.current_invoker=None
        self.current_vision_callback=None
        self.current_expected_result=None
        self.tolerance = tolerance
        self.mapper=Mapper()
        Feedback.feedbackers.append(self)
    
    #request async or request+send back? 
    def request_feedback(self, invoker, vision_callback:function, abstraction_callback:function,expected_result:()):
        self.current_invoker=invoker
        self.current_expected_result = expected_result
        self.current_vision_callback = vision_callback
        self.current_abstraction_callback = abstraction_callback
        return self.main()
    
    
    def take_screenshot(self):
        pass

    def compare_with_expected(self,actual)->bool:
        return np.all(np.isin(self.current_expected_result, actual))

    def board_is_stable(self, img1, img2):
        if img1 == img2:
            return True
        difference = cv2.subtract(img1, img2)
        b, g, r = cv2.split(difference)

        if cv2.countNonZero(b) <= self.tolerance and cv2.countNonZero(g) <= self.tolerance and cv2.countNonZero(r) <= self.tolerance:
            return True
        return False

    def get_mapped(self,to_map):
        to_return=[]
        for element in to_map:
            if issubclass(type(element),Predicate):
                to_return.append( self.mapper.get_string(element))
        return to_return

    def main(self):
        screenshot_to_compare1 = self.take_screenshot()
        while True:
            screenshot_to_compare2 = self.take_screenshot()
            if not self.board_is_stable(screenshot_to_compare1,screenshot_to_compare2):
                screenshot_to_compare1 = screenshot_to_compare2
                sleep(0.5)
            else:
                vision_result = self.current_vision_callback()
                abstraction_result = self.current_abstraction_callback(vision_result)
                mapped_objects = self.get_mapped(abstraction_result)
                return (self.compare_with_expected(mapped_objects),abstraction_result)
   