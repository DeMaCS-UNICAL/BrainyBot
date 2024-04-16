import os

from base.option_descriptor import OptionDescriptor
from languages.asp.asp_input_program import ASPInputProgram
from languages.asp.asp_mapper import ASPMapper
from languages.asp.answer_sets import *

from AI.src.g2048.dlvsolution.helpers import chooseDLVSystem, Node, Superior, Left, Value, Direction
from AI.src.g2048.constants import RESOURCES_PATH

class DLVSolution:

    def __init__(self):
        try:
            self.__handler = chooseDLVSystem()
            self.__static_facts = ASPInputProgram()
            self.__dinamic_facts = ASPInputProgram()
            self.__fixed_input_program = ASPInputProgram()
        except Exception as e:
            print(str(e))

    def __init_fixed(self, encoding : str):
        self.__fixed_input_program.add_files_path(os.path.join(RESOURCES_PATH, encoding))

    def __init_static(self, nodes : list, superior : list, left : list):
        for n in nodes:
            self.__static_facts.add_object_input(n)

        for s in superior:
            self.__static_facts.add_object_input(s)

        for l in left:
            self.__static_facts.add_object_input(l)

    def __init_dinamic(self, value : list):
        for v in value:
            self.__dinamic_facts.add_object_input(v)

    def start_asp(self, encoding :str, nodes : list, superior : list, left : list):
        ASPMapper.get_instance().register_class(Node)
        ASPMapper.get_instance().register_class(Superior)
        ASPMapper.get_instance().register_class(Left)
        ASPMapper.get_instance().register_class(Value)
        ASPMapper.get_instance().register_class(Direction)

        self.__init_fixed(encoding)
        self.__init_static(nodes, superior, left)

        option = OptionDescriptor("--filter=direction\1")
        self.__handler.add_option(option)

        self.__handler.add_program(self.__fixed_input_program)
        self.__handler.add_program(self.__static_facts)

    def recall_asp(self, value : list):
        self.__handler.remove_program_from_value(self.__dinamic_facts)
        self.__dinamic_facts = ASPInputProgram()
        self.__init_dinamic(value)

        answer_sets : AnswerSets = self.__handler.start_sync()

        print(len(answer_sets.get_optimal_answer_sets()))



        return
        
        

