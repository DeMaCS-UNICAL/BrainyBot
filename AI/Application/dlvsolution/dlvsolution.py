import os

from languages.asp.asp_input_program import ASPInputProgram

from Application.costants import RESOURCES_PATH
from Application.dlvsolution.helpers import chooseDLVSystem, InputNode, Edge, Swap


class DLVSolution:

    def __init__(self, nodes: [InputNode]):
        self.__nodes = nodes

        try:
            self.__handler = chooseDLVSystem()
            self.__variableInputProgram = None
            self.__fixedInputProgram = ASPInputProgram()

            self.__initFixed()
        except Exception as e:
            print(str(e))

    def __initFixed(self):
        self.__fixedInputProgram.add_files_path(os.path.join(RESOURCES_PATH, "rules.dlv2"))
        for node in self.__nodes:
            self.__fixedInputProgram.add_object_input(node)
        self.__handler.add_program(self.__fixedInputProgram)

    def recallASP(self, edges: [Edge]) -> Swap:
        try:
            self.__variableInputProgram = ASPInputProgram()
            for edge in edges:  # add edges input to dlvsolution program
                self.__variableInputProgram.add_object_input(edge)

            index = self.__handler.add_program(self.__variableInputProgram)
            answerSets = self.__handler.start_sync()

            swap = None
            for answerSet in answerSets.get_optimal_answer_sets():
                print(answerSet)
                for obj in answerSet.get_atoms():
                    if isinstance(obj, Swap):
                        swap = Swap(obj.get_id1(), obj.get_id2())

            self.__handler.remove_program_from_id(index)
            return swap

        except Exception as e:
            print(str(e))
