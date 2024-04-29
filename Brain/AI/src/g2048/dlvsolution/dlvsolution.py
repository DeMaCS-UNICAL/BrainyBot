import os

from base.option_descriptor import OptionDescriptor
from languages.asp.asp_input_program import ASPInputProgram
from languages.asp.asp_mapper import ASPMapper
from languages.asp.answer_sets import *

from AI.src.g2048.dlvsolution.helpers import chooseDLVSystem, Node, Superior, Left, Value, Direction, Output
from AI.src.g2048.constants import RESOURCES_PATH

class DLVSolution:

    def __init__(self):
        try:
            self.__index = None
            self.__handler = chooseDLVSystem()
            self.__static_facts = ASPInputProgram()
            self.__dinamic_facts = ASPInputProgram()
            self.__fixed_input_program = ASPInputProgram()
            self.__gameOver = False
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

    def isGameOver(self):
        return self.__gameOver

    def start_asp(self, encoding :str, nodes : list, superior : list, left : list):
        ASPMapper.get_instance().register_class(Node)
        ASPMapper.get_instance().register_class(Superior)
        ASPMapper.get_instance().register_class(Left)
        ASPMapper.get_instance().register_class(Value)
        ASPMapper.get_instance().register_class(Direction)
        ASPMapper.get_instance().register_class(Output)

        self.__init_fixed(encoding)
        self.__init_static(nodes, superior, left)

        self.__handler.add_program(self.__fixed_input_program)
        self.__handler.add_program(self.__static_facts)

    def recall_asp(self, value : list):
        if self.__index != None:
            self.__handler.remove_program_from_id(self.__index)
        self.__dinamic_facts = ASPInputProgram()
        self.__init_dinamic(value)
        self.__index = self.__handler.add_program(self.__dinamic_facts)

        answer_sets : AnswerSets = self.__handler.start_sync()

        oas = answer_sets.get_optimal_answer_sets()

        if len(oas) == 0:
            self.__gameOver = True
            return None, None
        
        dir = None
        output = []
        
        for answer_set in oas:
            for obj in answer_set.get_atoms():
                if isinstance(obj, Direction):
                    dir = obj.get_dir()
                elif isinstance(obj, Output):
                    output.append(obj)

        return dir, output
        
        

