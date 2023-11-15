import os

from languages.asp.asp_input_program import ASPInputProgram

from AI.src.constants import RESOURCES_PATH
from AI.src.candy_crush.dlvsolution.helpers import chooseDLVSystem

class Validation:
    def __init__(self,asp_validator):
        try:
            self.__handler = chooseDLVSystem()
            self.__variableInputProgram = None
            self.__fixedInputProgram = ASPInputProgram()
            print (f"Looking for validator at {os.path.join(RESOURCES_PATH, asp_validator)}")
            self.__fixedInputProgram.add_files_path(os.path.join(RESOURCES_PATH, asp_validator))
            self.__handler.add_program(self.__fixedInputProgram)

        except Exception as e:
            print(str(e))
    
    def validate(self, abstraction_result):
        self.__handler.remove_program_from_value(self.__variableInputProgram)
        self.__variableInputProgram = ASPInputProgram()
        for element in abstraction_result:
                print(element)
                self.__variableInputProgram.add_object_input(element)
        index = self.__handler.add_program(self.__variableInputProgram)
        answerSets = self.__handler.start_sync()
        print (f"Answer sets: {answerSets.get_output()}")
        print (f"Answer sets: {answerSets.get_errors()}")
        if not answerSets.get_answer_sets():
            print("Validation failed, no answer set provided")
        else:
            for obj in answerSets.get_answer_sets()[0].get_answer_set():
                if(obj.startswith('toPrint(')):
                    print(obj[8:])
            