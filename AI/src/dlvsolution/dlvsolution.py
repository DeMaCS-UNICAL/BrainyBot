import os

from languages.asp.asp_input_program import ASPInputProgram

from src.constants import RESOURCES_PATH
from src.dlvsolution.helpers import chooseDLVSystem, InputNode, Edge, Swap

failureException = ValueError

def assertTrue(expr, msg=None):
        """Check that the expression is true."""
        if not expr:
            msg = f"{msg}: {(expr)} is not true"
            raise failureException(msg)


class DLVSolution:

    def __init__(self):
        try:
            self.__handler = chooseDLVSystem()
            self.__variableInputProgram = None
            self.__fixedInputProgram = ASPInputProgram()

            self.__initFixed()
        except Exception as e:
            print(str(e))

    def __initFixed(self):
        self.__fixedInputProgram.add_files_path(os.path.join(RESOURCES_PATH, "rules.dlv2"))
        self.__handler.add_program(self.__fixedInputProgram)

    def recallASP(self, edges: [Edge], nodes: [InputNode]) -> Swap:
        try:
            self.__variableInputProgram = ASPInputProgram()

            # insert nodes from graph to asp program
            for node in nodes:
                #print(node)
                self.__variableInputProgram.add_object_input(node)

            for edge in edges:  # add edges input to dlv solution program
                self.__variableInputProgram.add_object_input(edge)

            index = self.__handler.add_program(self.__variableInputProgram)
            answerSets = self.__handler.start_sync()

            #assertTrue(answerSets is not None)
            #assertTrue(isinstance(answerSets, Swap),
            #                "Error, result object is not Swap")
            assertTrue(answerSets.get_errors() == "",
                            "Found error:\n" + str(answerSets.get_errors()))
            assertTrue(len(answerSets.get_optimal_answer_sets()) != 0)

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
