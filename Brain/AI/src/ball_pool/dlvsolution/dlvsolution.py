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

    def __init_static_facts(self, colors: list, balls: list, pockets: list):
        for color in colors:
            self.__static_facts.add_object_input(color)

        for ball in balls:
            self.__static_facts.add_object_input(ball)

        for pocket in pockets:
            self.__static_facts.add_object_input(pocket)
        
        #self.__static_facts.add_program("numPockets(" + str(len(pockets)) + ").")

    """
        print("Colors:", [str(c) for c in colors])
        print("Balls:", [str(b) for b in balls])
        print("Pockets:", [str(p) for p in pockets])
    """



    def __init_dinamic_facts(self, dynamic_facts: list):
        for facts in dynamic_facts:
            self.__dinamic_facts.add_object_input(facts)

    def __init_fixed(self):
        self.__fixed_input_program.add_files_path(os.path.join(RESOURCES_PATH, "ballPool.asp"))

    def call_asp(self, balls, pockets):

        ASPMapper.get_instance().register_class(Color)
        ASPMapper.get_instance().register_class(Ball)
        ASPMapper.get_instance().register_class(Pocket)
        ASPMapper.get_instance().register_class(MoveAndShoot)
        ASPMapper.get_instance().register_class(GameOver)

        self.__init_static_facts( [], balls, pockets)
        self.__init_dinamic_facts([]) #TO REVIEW
        self.__init_fixed()

        self.__handler.add_program(self.__static_facts)
        self.__handler.add_program(self.__dinamic_facts)
        self.__handler.add_program(self.__fixed_input_program)

        option = OptionDescriptor("--filter=moveandshoot/3, gameOver/1")
        self.__handler.add_option(option)

        """
        print("Static facts:")
        print(self.__static_facts.get_program_string())  # se il metodo esiste, oppure un modo per ottenere la stringa
        print("Dinamic facts:")
        print(self.__dinamic_facts.get_program_string())
        print("Fixed program:")
        print(self.__fixed_input_program.get_program_string())
        """

        moves = []
        game_over = False
        step = 1

        while not game_over and step <= MAX_STEPS:
            # for a in range(0,LOOK_AHEAD):
            self.__dinamic_facts.add_program(f"step({str(step)}).")


            answer_sets = self.__handler.start_sync()
            self.__dinamic_facts.clear_all()

            print (f"Answer sets: {len(answer_sets.get_optimal_answer_sets())}")
            assert_true(answer_sets is not None,"No solutions found for this match.")
            print(f"Answer sets: {answer_sets}")
            assert_true(len(answer_sets.get_optimal_answer_sets()) != 0,"No optimal solutions found for this match.")

            for answer_set in answer_sets.get_optimal_answer_sets():
                for obj in answer_set.get_atoms():
                    if isinstance(obj, MoveAndShoot):
                        if obj.get_step() == step:
                            self.__dinamic_facts.add_object_input(obj)
                            moves.append(obj)

                    if isinstance(obj, GameOver):
                        game_over = True
                break 
            step+=1

        return moves
