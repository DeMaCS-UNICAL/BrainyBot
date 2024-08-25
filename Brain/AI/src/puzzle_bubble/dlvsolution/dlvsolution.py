import os
import random
from languages.asp.asp_input_program import ASPInputProgram

from AI.src.puzzle_bubble.constants import RESOURCES_PATH
from AI.src.puzzle_bubble.dlvsolution.helpers import Bubble, Move, chooseDLVSystem

class DLVSolution:

    def __init__(self):
        try:
            self.__handler = chooseDLVSystem()
            self.__variableInputProgram = None
            self.__fixedInputProgram = ASPInputProgram()
            self.__aspInputFile = 'rules.dlv2'

            self.__init_fixed()
        except Exception as e:
            print(str(e))

    def __init_fixed(self):
        print (f"Looking for rules in {os.path.join(RESOURCES_PATH, self.__aspInputFile)}")
        self.__fixedInputProgram.add_files_path(os.path.join(RESOURCES_PATH, self.__aspInputFile))
        self.__handler.add_program(self.__fixedInputProgram)

    def recall_asp(self, input):
        try:
            print (f"Calling ASP Solver.")
            
            self.__handler.remove_program_from_value(self.__variableInputProgram)
            self.__variableInputProgram = ASPInputProgram()
            print (f"Created ASP program.")
            
            for element in input:
                self.__variableInputProgram.add_object_input(element)
            print (f"Created Inputs.")
            
            index = self.__handler.add_program(self.__variableInputProgram)
            print (f"Let's start the solver.")
            answerSets = self.__handler.start_sync()
            print (f"Answer sets: {answerSets.get_output()}")

            move = None
            #We will need to set get_optimal_answer_sets() after adding weak constraints.
            for answerSet in answerSets.get_optimal_answer_sets():
                for obj in answerSet.get_atoms():
                    if isinstance(obj, Move):
                        move = Move(obj.get_index(),obj.get_angle(),obj.get_col(),obj.get_row())
                        break

            self.__handler.remove_program_from_id(index)
            return move

        except Exception as e:
            print(str(e))
