from AI.src.constants import SCREENSHOT_FULLPATH, BENCHMARK_PATH
import os
import time

class BenchmarkUtils:
    def __init__(self, game_name):
        self.game_name = game_name
        self.step_index = 0
        self.level_index = 0
        self.__build_benchmark_matrix()
        self.benchmark_file = None
        self.timer = None
        self.load_current_level()
    
    def __build_benchmark_matrix(self):
        self.benchmark_matrix = []
        levels = os.listdir(os.path.join(BENCHMARK_PATH, self.game_name))
        levels.sort()
        for level in levels:
            level_steps = os.listdir(os.path.join(BENCHMARK_PATH, self.game_name, level))
            level_steps.sort(key=lambda x: int(x.split('_')[1].split('.')[0]))
            level_steps_paths = [os.path.join(BENCHMARK_PATH, self.game_name, level, step) for step in level_steps]
            self.benchmark_matrix.append(level_steps_paths)

    
    def is_level_finished(self):
        return self.step_index == len(self.benchmark_matrix[self.level_index])
    
    def is_game_finished(self):
        return self.level_index == len(self.benchmark_matrix)
    
    def load_new_level(self):
        self.step_index = 0
        self.level_index += 1
        if self.is_game_finished():
            return False
        os.system(f'cp {self.benchmark_matrix[self.level_index][self.step_index]} {SCREENSHOT_FULLPATH}')
        return True

    def load_new_step(self):
        self.step_index += 1
        if self.is_level_finished():
            return False
        os.system(f'cp {self.benchmark_matrix[self.level_index][self.step_index]} {SCREENSHOT_FULLPATH}')
        return True    
    
    def restart(self):
        self.step_index = 0
        self.level_index = 0
        return True
    
    def start_timer(self):
        self.timer = time.time()

    def stop_timer(self):
        self.timer = time.time() - self.timer

    def save_time(self, level, step, type):
        if not self.benchmark_file:
            self.benchmark_file = open(f"{self.game_name}_benchmark.csv", "w")
            self.benchmark_file.write("level,step,type,time\n")
        self.benchmark_file.write(f"{level},{step},{type},{self.timer}\n")

    def end_benchmark(self, sort=False):
        if self.benchmark_file:
            self.benchmark_file.close()
            if not sort:
                print("Benchmark finished - no sorting")
                return
                
            with open(f"{self.game_name}_benchmark.csv", "r") as file:
                lines = file.readlines()

            header = lines[0]
            data = lines[1:]
            data.sort(key=lambda x: (int(x.split(',')[0]), int(x.split(',')[1].split('_')[1]), x.split(',')[2]))
            with open(f"{self.game_name}_benchmark.csv", "w") as file:
                file.write(header)
                file.writelines(data)

            print("Benchmark finished - sorted")

           
    
    def get_level_name(self):
        return os.path.basename(os.path.dirname(self.benchmark_matrix[self.level_index][0]))
    
    def get_step_name(self):
        return os.path.basename(self.benchmark_matrix[self.level_index][self.step_index].split('.')[0])
    
    def load_current_level(self):
        os.system(f'cp {self.benchmark_matrix[self.level_index][self.step_index]} {SCREENSHOT_FULLPATH}')
        return True