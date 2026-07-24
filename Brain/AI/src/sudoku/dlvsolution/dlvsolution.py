import os

from languages.asp.asp_input_program import ASPInputProgram
from languages.asp.asp_mapper import ASPMapper
from languages.asp.answer_sets import *

from AI.src.sudoku.dlvsolution.helpers import chooseDLVSystem, Cell, Box, Given, Value
from AI.src.sudoku.constants import RESOURCES_PATH


class DLVSolution:

    def __init__(self):
        self.__handler = chooseDLVSystem()

    def solve(self, cells, boxes, givens):
        ASPMapper.get_instance().register_class(Cell)
        ASPMapper.get_instance().register_class(Box)
        ASPMapper.get_instance().register_class(Given)
        ASPMapper.get_instance().register_class(Value)

        fixed_program = ASPInputProgram()
        fixed_program.add_files_path(os.path.join(RESOURCES_PATH, "encoding.asp"))

        facts_program = ASPInputProgram()
        for c in cells:
            facts_program.add_object_input(c)
        for b in boxes:
            facts_program.add_object_input(b)
        for g in givens:
            facts_program.add_object_input(g)

        self.__handler.add_program(fixed_program)
        self.__handler.add_program(facts_program)

        answer_sets: AnswerSets = self.__handler.start_sync()
        # The encoding has no weak constraints, so get_optimal_answer_sets()
        # would crash (ValueError: max() arg is an empty sequence) trying to
        # rank answer sets by weight. Use the plain answer sets instead.
        oas = answer_sets.get_answer_sets()

        if len(oas) == 0:
            return None

        values = []
        for answer_set in oas[0:1]:
            for obj in answer_set.get_atoms():
                if isinstance(obj, Value):
                    values.append(obj)
        return values
