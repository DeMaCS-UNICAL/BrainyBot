import os

from base.option_descriptor import OptionDescriptor
from languages.asp.asp_input_program import ASPInputProgram
from languages.asp.asp_mapper import ASPMapper

from AI.src.ball_sort.constants import RESOURCES_PATH, MAX_STEPS, LOOK_AHEAD
from AI.src.ball_sort.dlvsolution.helpers import choose_dlv_system, Color, Ball, Tube, Move, On, GameOver
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

    def __init_static_facts(self, colors: [], balls: [], tubes: []):
        for color in colors:
            self.__static_facts.add_object_input(color)

        for ball in balls:
            self.__static_facts.add_object_input(ball)

        tube_size = 0
        full_tube = 0
        for tube in tubes:
            self.__static_facts.add_object_input(tube)
            if len(tube.get_balls()) > 0:
                tube_size = len(tube.get_balls())
                full_tube += 1

        #self.__static_facts.add_program("tubeSize(" + str(tube_size) + ").")
        #self.__static_facts.add_program("fullTube(" + str(full_tube) + ").")


    def __init_dinamic_facts(self, on: []):
        for o in on:
            self.__dinamic_facts.add_object_input(o)

    def __init_fixed(self):
        self.__fixed_input_program.add_files_path(os.path.join(RESOURCES_PATH, "ballSort.asp"))

    def call_asp(self, colors: [], balls: [], tubes: [], on: []):

        ASPMapper.get_instance().register_class(Color)
        ASPMapper.get_instance().register_class(Ball)
        ASPMapper.get_instance().register_class(Tube)
        ASPMapper.get_instance().register_class(Move)
        ASPMapper.get_instance().register_class(On)
        ASPMapper.get_instance().register_class(GameOver)

        self.__init_static_facts(colors, balls, tubes)
        self.__init_dinamic_facts(on)
        self.__init_fixed()

        self.__handler.add_program(self.__static_facts)
        self.__handler.add_program(self.__dinamic_facts)
        self.__handler.add_program(self.__fixed_input_program)

        option = OptionDescriptor("--filter=on/4, move/3, gameOver/1, feedback_on_color/4, wrongPlace/1, wrongs/1, freeToMove/1, singleColorTubeWithColorMax/3")
        self.__handler.add_option(option)

        moves = []
        ons = []
        game_over = False
        
        ans=[]
        step = 1
        while not game_over and step <= MAX_STEPS:
            # for a in range(0,LOOK_AHEAD):
            self.__dinamic_facts.add_program(f"step({str(step)}).")

            answer_sets = self.__handler.start_sync()

            self.__dinamic_facts.clear_all()
            print (f"Answer sets: {len(answer_sets.get_optimal_answer_sets())}")
            assert_true(answer_sets is not None,"No solutions found for this level.")
            
            print(answer_sets.get_errors())
            print(answer_sets._errors)
            #assert_true(answer_sets.get_errors() is None,
            #            "Found error:\n" + str(answer_sets.get_errors()))
            assert_true(len(answer_sets.get_optimal_answer_sets()) != 0,"No optimal solutions found for this level.")
            for answer_set in answer_sets.get_optimal_answer_sets():
                print(answer_set)
                ans.append(answer_set)
                for obj in answer_set.get_atoms():
                    if isinstance(obj, Move):
                        print(obj.get_ball(),obj.get_tube(),obj.get_step())
                        if obj.get_step() == step:
                        #if step <= obj.get_step() < step+LOOK_AHEAD:
                            self.__dinamic_facts.add_object_input(obj)
                            moves.append(obj)

                    if isinstance(obj, On):
                        if obj.get_step() == 1:
                        #if 1 <= obj.get_step() < step+LOOK_AHEAD:
                            ons.append(obj)
                        if obj.get_step() == step + 1:
                        #if step + 1 <= obj.get_step() < step+LOOK_AHEAD:
                            self.__dinamic_facts.add_object_input(obj)
                            ons.append(obj)

                    if isinstance(obj, GameOver):
                        game_over = True
                break # GB: 16 9 2023. Will not look a more than one optimal answer set
            #step += LOOK_AHEAD
            step+=1

        return moves, ons, ans