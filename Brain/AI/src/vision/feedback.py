
import numpy as np
from languages.asp.asp_mapper import ASPMapper
from languages.predicate import Predicate
from time import sleep
from AI.src.webservices.helpers import getScreenshot
from AI.src.abstraction.helpers import getImg
from AI.src.constants import SCREENSHOT_PATH, SCREENSHOT_FILENAME
import constants
from matplotlib import pyplot as plt

class Feedback:
    def __init__(self, tolerance=0):
        self.current_vision_callback=None
        self.current_expected_result=[]
        self.current_abstraction_callback = None
        self.tolerance = tolerance
        self.mapper=ASPMapper.get_instance()
    
    def request_feedback(self, vision_callback, abstraction_callback, abstraction_to_asp,expected_result):
        self.current_expected_result = []
        self.current_vision_callback = vision_callback
        self.current_abstraction_callback = abstraction_callback
        self.current_abstraction_to_asp_callback = abstraction_to_asp
        for obj in expected_result.get_answer_set():
            if(obj.startswith('feedback_')):
                self.current_expected_result.append(obj[9:])
        return self.main()
    
    
    def take_screenshot(self):
        server_ip, port = constants.SCREENSHOT_SERVER_IP, 5432
        try:
            getScreenshot(server_ip, port)
            print("SCREENSHOT TAKEN.")
        except Exception as e:
            print(e)
            exit(1)

    def compare_with_expected(self,actual)->bool:
        print(self.current_expected_result)
        print("______________________________________")
        print(actual)
        to_return= True
        for x in self.current_expected_result:
            if not np.isin(x, actual).any():
                print(x)
                to_return=False
                break
        print("success? ",to_return)
        self.current_expected_result=[]
        return to_return

    def board_is_stable(self, abstr1, abstr2):
        if np.isin(abstr1,abstr2).any():
            return True
        return False

    def get_mapped(self,to_map):
        to_return=[]
        for element in to_map:
            if issubclass(type(element),Predicate):
                to_return.append( self.mapper.get_string(element))
        return to_return

    def main(self):
        self.take_screenshot()
        vision_result = self.current_vision_callback()
        abstraction_result = self.current_abstraction_callback(vision_result)
        asp_input=self.current_abstraction_to_asp_callback(abstraction_result)
        mapped_objects1 = self.get_mapped(asp_input[0])
        while True:
            self.take_screenshot()
            vision_result = self.current_vision_callback()
            abstraction_result = self.current_abstraction_callback(vision_result)
            asp_input=self.current_abstraction_to_asp_callback(abstraction_result)
            mapped_objects2 = self.get_mapped(asp_input[0])
            if not self.board_is_stable(mapped_objects1,mapped_objects2):
                mapped_objects1 = mapped_objects2
            else:
                return (self.compare_with_expected(mapped_objects2),abstraction_result,asp_input)
   