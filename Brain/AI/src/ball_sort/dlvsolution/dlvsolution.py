import os

from base.option_descriptor import OptionDescriptor
from languages.asp.asp_input_program import ASPInputProgram
from languages.asp.asp_mapper import ASPMapper

from AI.src.ball_sort.constants import RESOURCES_PATH, MAX_STEPS, LOOK_AHEAD
from AI.src.ball_sort.dlvsolution.helpers import choose_incremental_system,choose_dlv_system,choose_clingo_system, Color, Ball, Tube, Move, On, GameOver
from AI.src.candy_crush.dlvsolution.helpers import assert_true


class DLVSolution:

    def __init__(self):
        try:
            
            ASPMapper.get_instance().register_class(Color)
            ASPMapper.get_instance().register_class(Ball)
            ASPMapper.get_instance().register_class(Tube)
            ASPMapper.get_instance().register_class(Move)
            ASPMapper.get_instance().register_class(On)
            ASPMapper.get_instance().register_class(GameOver)
            #self.__handler = choose_dlv_system()
            self.__handler = choose_incremental_system()
            #self.__handler = choose_clingo_system()
            self.__static_facts = ASPInputProgram()
            self.__dinamic_facts = ASPInputProgram()
            self.__fixed_input_program = ASPInputProgram()
            self.__init_fixed()
            self.__handler.add_program(self.__fixed_input_program,True)

        except Exception as e:
            print(e)

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

        self.__static_facts.add_program("tubeSize(" + str(tube_size) + ").")
        self.__static_facts.add_program("fullTube(" + str(full_tube) + ").")


    def __init_dinamic_facts(self, on: []):
        for o in on:
            self.__dinamic_facts.add_object_input(o)

    def __init_fixed(self):
        #self.__fixed_input_program.add_files_path(os.path.join(RESOURCES_PATH, "ballSort.txt"))
        self.__fixed_input_program.add_files_path(os.path.join(RESOURCES_PATH, "ballSort_dns_choice.asp"))

    def call_asp(self, colors: [], balls: [], tubes: [], on: []):


        self.__init_static_facts(colors, balls, tubes)
        self.__init_dinamic_facts(on)
        self.__init_fixed()


        #option = OptionDescriptor("--filter=on/4, move/3, gameOver/1")
        #option = OptionDescriptor("--filter=move/3, gameOver/1")
        #option = OptionDescriptor("--print-rewriting")
        #self.__handler.add_option(option)

        moves = []
        ons = []
        game_over = False

        step = 1
        while not game_over and step <= MAX_STEPS:
            moves = []
            ons = []
            # for a in range(0,LOOK_AHEAD):
            self.__static_facts.add_program(f"step({str(step)}).")
            #print(self.__static_facts.get_programs())
            #print(self.__dinamic_facts.get_programs())
            #self.__handler.add_program(self.__static_facts)
            #self.__handler.add_program(self.__dinamic_facts)
            file_path="ball_sort_facts.asp"
            with open(os.path.join(RESOURCES_PATH,file_path), "w") as file:
                file.write(self.__static_facts.get_programs())
                file.write(self.__dinamic_facts.get_programs())
            temp = ASPInputProgram()
            temp.add_files_path(os.path.join(RESOURCES_PATH,file_path))
            self.__handler.add_program(temp)
            answer_sets = self.__handler.start_sync()

            #self.__dinamic_facts.clear_all()

            #print (f"Answer sets: {len(answer_sets.get_optimal_answer_sets())}")
            print (f"Answer sets: {len(answer_sets.get_answer_sets())}")
            print(f"Errors:{str(answer_sets.get_errors())}")
            #assert_true(answer_sets is not None,"No solutions found for this level.")
            
            #assert_true(answer_sets.get_errors() is None,
                        #"Found error:\n" + str(answer_sets.get_errors()))
            no_ans=False
            answer_sets_result = answer_sets.get_answer_sets() if len(answer_sets.get_optimal_answer_sets()) == 0 else answer_sets.get_optimal_answer_sets()
            
            #assert_true(len(answer_sets_result)!=0,"No optimal solutions found for this level.")

            for answer_set in answer_sets_result:
                for obj in answer_set.get_atoms():
                    #print(obj)
                    if isinstance(obj, On):
                        #if obj.get_step() == 1:
                        #if 1 <= obj.get_step() < step+LOOK_AHEAD:
                        #    ons.append(obj)
                        #if obj.get_step() == step + 1:
                        #if step + 1 <= obj.get_step() < step+LOOK_AHEAD:
                            #self.__dinamic_facts.add_object_input(obj)
                        ons.append(obj)
                    if isinstance(obj, Move):
                        #if obj.get_step() == step:
                        #if step <= obj.get_step() < step+LOOK_AHEAD:
                            #self.__dinamic_facts.add_object_input(obj)
                        moves.append(obj)
                    if isinstance(obj, GameOver):
                        game_over = True
                break # GB: 16 9 2023. Will not look a more than one optimal answer set
            #step += LOOK_AHEAD
            print(step,"Gameover?",game_over,"moves:",moves)
            if game_over:
                break
            else:
                moves=[]
                ons=[]
            step+=1
        self.__handler.quit()

        return moves, ons
