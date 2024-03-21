import os

from languages.asp.asp_input_program import ASPInputProgram

from AI.src.candy_crush.constants import RESOURCES_PATH
from AI.src.candy_crush.dlvsolution.helpers import chooseDLVSystem, InputNode, Edge, Swap, assert_true


class DLVSolution:

    def __init__(self):
        try:
            self.__handler = chooseDLVSystem()
            self.__variableInputProgram = None
            self.__fixedInputProgram = ASPInputProgram()

            self.__init_fixed()
        except Exception as e:
            print(str(e))

    def __init_fixed(self):
        print (f"Looking for rules in {os.path.join(RESOURCES_PATH, 'rules.dlv2')}")
        self.__fixedInputProgram.add_files_path(os.path.join(RESOURCES_PATH, "rules.dlv2"))
        self.__handler.add_program(self.__fixedInputProgram)

    def recall_asp(self, input):
        try:
            print (f"Calling ASP Solver.")
            
            self.__handler.remove_program_from_value(self.__variableInputProgram)
            self.__variableInputProgram = ASPInputProgram()
            print (f"Created ASP program.")
            
            # insert nodes from graph to asp program
            for element in input:
                #print(element)
                self.__variableInputProgram.add_object_input(element)
            print (f"Created Nodes.")
            
            '''
            for edge in edges:  # add edges input to dlv solution program
                self.__variableInputProgram.add_object_input(edge)
            print (f"Created Edges.")
            '''
            index = self.__handler.add_program(self.__variableInputProgram)
            print (f"Let's start the solver.")
            answerSets = self.__handler.start_sync()
            print (f"Answer sets: {answerSets.get_output()}")
            #assert_true(answerSets is not None)
            #assert_true(isinstance(answerSets, Swap),
            #                "Error, result object is not Swap")
            #assert_true(answerSets.get_errors() == "",
            #            "Found error:\n" + str(answerSets.get_errors()))
            #assert_true(len(answerSets.get_optimal_answer_sets()) != 0)

            swap = None
            as_to_return = None
            for answerSet in answerSets.get_optimal_answer_sets():
                print(answerSet)
                for obj in answerSet.get_atoms():
                    print(obj)
                    if isinstance(obj, Swap):
                        swap = Swap(obj.get_id1(), obj.get_id2())
                        as_to_return = answerSet

            self.__handler.remove_program_from_id(index)
            return swap,as_to_return

        except Exception as e:
            print(str(e))
