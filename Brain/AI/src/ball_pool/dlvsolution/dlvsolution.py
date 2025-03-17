import os

from base.option_descriptor import OptionDescriptor
from languages.asp.asp_input_program import ASPInputProgram
from languages.asp.asp_mapper import ASPMapper

from AI.src.ball_pool.constants import RESOURCES_PATH, MAX_STEPS, LOOK_AHEAD
from AI.src.ball_pool.dlvsolution.helpers import choose_dlv_system, Color, Ball, Pocket, MoveAndShoot, GameOver
from AI.src.candy_crush.dlvsolution.helpers import assert_true


class DLVSolution: 

    def __init__(self):
        try:
            self.__handler = choose_dlv_system()
            self.__static_facts = ASPInputProgram()
            self.__dinamic_facts = ASPInputProgram()
            self.__fixed_input_program = ASPInputProgram()

        except Exception as e:
            print(str(e))

    def __init_static_facts(self, balls: list, pockets: list):
        for ball in balls:
            self.__static_facts.add_object_input(ball)

        for pocket in pockets:
            self.__static_facts.add_object_input(pocket)
        



    def __init_dinamic_facts(self, dinamic_facts : []):
        for dinamic_fact in dinamic_facts:
            self.__dinamic_facts.add_object_input(dinamic_fact)
    
    def __init_fixed(self):
        self.__fixed_input_program.add_files_path(os.path.join(RESOURCES_PATH, "ballPool.asp"))

    def call_asp(self,balls, pockets, aim_situation):

        ASPMapper.get_instance().register_class(Ball)
        ASPMapper.get_instance().register_class(Pocket)
        ASPMapper.get_instance().register_class(MoveAndShoot)
        ASPMapper.get_instance().register_class(GameOver)

        self.__init_static_facts(balls, pockets )
        self.__init_dinamic_facts(aim_situation) 
        self.__init_fixed()

        self.__handler.add_program(self.__static_facts)
        self.__handler.add_program(self.__dinamic_facts)
        self.__handler.add_program(self.__fixed_input_program)

        option = OptionDescriptor("--filter=moveandshoot/6,  ball/0, pocket/2, aimline/4, gameOver/1")
        self.__handler.add_option(option)


        moves = []
        ans = []
        game_over = False
        step = 1

        while not game_over and step <= MAX_STEPS:
            # for a in range(0,LOOK_AHEAD):
            self.__dinamic_facts.add_program(f"step({str(step)}).")

            answer_sets = self.__handler.start_sync()
            self.__dinamic_facts.clear_all()

            result = answer_sets.get_answer_sets()
            print (f"Answer sets: {len(result)}")
            assert_true(answer_sets is not None,"No solutions found for this match.")

            print(f"Answer sets: {answer_sets}")
            assert_true(len(result) != 0,"No optimal solutions found for this match.")

            for answer_set in result:
                print(answer_set)
                ans.append(answer_set)
                for obj in answer_set.get_atoms():
                    if isinstance(obj, MoveAndShoot):
                        #print(obj.get_ball(),obj.get_pocket(),obj.get_step())
                        if obj.get_step() == step:
                            self.__dinamic_facts.add_object_input(obj)
                            moves.append(obj)

                    if isinstance(obj, GameOver):
                        game_over = True
                break 
            step+=1

        return moves
