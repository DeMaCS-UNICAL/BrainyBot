import os
import time

class BenchmarkUtils:
    def __init__(self, game_name, resource_path):
        self.game_name = game_name
        to_strip = resource_path.rfind("screenshots")
        clean_path = resource_path[:to_strip]
        self.benchmark_path = os.path.join(clean_path, "benchmark")
        self.screenshots_path = os.path.join(clean_path, "screenshots")
        self.screenshot_path = os.path.join(self.screenshots_path, "temp.png")
        self.results_path = os.path.join(clean_path, "results")
        self.step_index = 0
        self.level_index = 0
        self.__build_benchmark_matrix()
        self.benchmark_file = None
        self.timer = None
        self.load_current_level()
    
    def __build_benchmark_matrix(self):
        self.benchmark_matrix = []
        
        # Controlla se la cartella benchmark esiste
        if not os.path.exists(self.benchmark_path):
            print(f"Warning: Benchmark folder not found at {self.benchmark_path}")
            return
        
        # Cerca tutti i file level_*.txt nella cartella benchmark
        try:
            level_files = [f for f in os.listdir(self.benchmark_path) if f.startswith('level_') and f.endswith('.txt')]
        except OSError as e:
            print(f"Error reading benchmark folder: {e}")
            return
        
        # Controlla se ci sono file di livello
        if not level_files:
            print(f"Warning: No level files found in {self.benchmark_path}")
            return
            
        level_files.sort(key=lambda x: int(x.split('_')[1].split('.')[0]))
        
        for level_file in level_files:
            level_file_path = os.path.join(self.benchmark_path, level_file)
            level_screenshots = []
            
            # Legge i nomi degli screenshot dal file
            try:
                with open(level_file_path, 'r') as f:
                    screenshot_names = [line.strip() for line in f.readlines() if line.strip()]
            except (OSError, IOError) as e:
                print(f"Error reading level file {level_file}: {e}")
                continue
            
            # Controlla se il file del livello è vuoto
            if not screenshot_names:
                print(f"Warning: Level file {level_file} is empty")
                continue
            
            # Costruisce i path completi degli screenshot
            for screenshot_name in screenshot_names:
                if not screenshot_name.endswith('.png'):
                    screenshot_name += '.png'
                screenshot_path = os.path.join(self.screenshots_path, screenshot_name)
                level_screenshots.append(screenshot_path)
            
            # Aggiunge il livello solo se contiene screenshot
            if level_screenshots:
                self.benchmark_matrix.append(level_screenshots)
        
        # Controlla se alla fine abbiamo almeno un livello valido
        if not self.benchmark_matrix:
            print("Warning: No valid levels found in benchmark files")

    
    def is_level_finished(self):
        if not self.benchmark_matrix or self.level_index >= len(self.benchmark_matrix):
            return True
        return self.step_index >= len(self.benchmark_matrix[self.level_index])
    
    def is_game_finished(self):
        return not self.benchmark_matrix or self.level_index >= len(self.benchmark_matrix)
    
    def load_new_level(self):
        self.step_index = 0
        self.level_index += 1
        if self.is_game_finished():
            return False
        os.system(f'cp {self.benchmark_matrix[self.level_index][self.step_index]} {self.screenshot_path}')
        return True

    def load_new_step(self):
        self.step_index += 1
        if self.is_level_finished():
            return False
        os.system(f'cp {self.benchmark_matrix[self.level_index][self.step_index]} {self.screenshot_path}')
        return True    
    
    def restart(self):
        self.step_index = 0
        self.level_index = 0
        return True
    
    def start_timer(self):
        self.timer = time.time()

    def stop_timer(self):
        if self.timer is not None:
            self.timer = time.time() - self.timer

    def save_time(self, level, step, type):
        if not self.benchmark_file:
            benchmark_file_path = os.path.join(self.results_path, f"{self.game_name}_benchmark.csv")
            self.benchmark_file = open(benchmark_file_path, "w")
            self.benchmark_file.write("level,step,name,type,time\n")
        self.benchmark_file.write(f"{self.level_index + 1},{self.step_index},{step},{type},{self.timer}\n")

    def end_benchmark(self, sort=False):
        if self.benchmark_file:
            self.benchmark_file.close()
            if not sort:
                print("Benchmark finished - no sorting")
                return
                
            benchmark_file_path = os.path.join(self.results_path, f"{self.game_name}_benchmark.csv")
            with open(benchmark_file_path, "r") as file:
                lines = file.readlines()

            header = lines[0]
            data = lines[1:]
            # Ordina per: level, step_index, type
            data.sort(key=lambda x: (int(x.split(',')[0]), int(x.split(',')[1]), x.split(',')[3]))
            with open(benchmark_file_path, "w") as file:
                file.write(header)
                file.writelines(data)

            print("Benchmark finished - sorted")
            
        # Crea automaticamente il file consuntivo
        self.create_summary_benchmark()
    
    def create_summary_benchmark(self):
        """Crea un file di benchmark consuntivo con statistiche aggregate"""
        if not self.benchmark_file:
            print("Warning: No benchmark data to summarize")
            return
            
        benchmark_file_path = os.path.join(self.results_path, f"{self.game_name}_benchmark.csv")
        summary_file_path = os.path.join(self.results_path, f"{self.game_name}_benchmark_summary.csv")
        
        # Verifica se il file benchmark esiste
        if not os.path.exists(benchmark_file_path):
            print(f"Warning: Benchmark file not found at {benchmark_file_path}")
            return
            
        try:
            # Legge i dati dal file benchmark
            with open(benchmark_file_path, "r") as file:
                lines = file.readlines()
            
            if len(lines) <= 1:
                print("Warning: No data found in benchmark file")
                return
                
            # Parsing dei dati (salta l'header)
            data = []
            for line in lines[1:]:
                parts = line.strip().split(',')
                if len(parts) >= 5:
                    level = int(parts[0])
                    step_index = int(parts[1])
                    name = parts[2]
                    type_op = parts[3]
                    time_val = float(parts[4])
                    data.append((level, step_index, name, type_op, time_val))
            
            # Calcola statistiche aggregate
            level_stats = {}
            
            for level, step_index, name, type_op, time_val in data:
                if level not in level_stats:
                    level_stats[level] = {
                        'steps': set(),
                        'types': {}
                    }
                
                level_stats[level]['steps'].add(step_index)
                
                if type_op not in level_stats[level]['types']:
                    level_stats[level]['types'][type_op] = []
                
                level_stats[level]['types'][type_op].append(time_val)
            
            # Scrive il file consuntivo
            with open(summary_file_path, "w") as file:
                file.write("level,num_steps,cache_avg_time,no_cache_avg_time,improvement_percentage\n")
                
                for level in sorted(level_stats.keys()):
                    num_steps = len(level_stats[level]['steps'])
                    
                    # Calcola tempi medi per cache e no cache
                    cache_avg = 0.0
                    no_cache_avg = 0.0
                    
                    if 'cache' in level_stats[level]['types']:
                        cache_times = level_stats[level]['types']['cache']
                        cache_avg = sum(cache_times) / len(cache_times)
                    
                    if 'no cache' in level_stats[level]['types']:
                        no_cache_times = level_stats[level]['types']['no cache']
                        no_cache_avg = sum(no_cache_times) / len(no_cache_times)
                    
                    # Calcola il miglioramento percentuale
                    improvement_percentage = 0.0
                    if no_cache_avg > 0 and cache_avg > 0:
                        improvement_percentage = ((no_cache_avg - cache_avg) / no_cache_avg) * 100
                    
                    file.write(f"{level},{num_steps},{cache_avg:.6f},{no_cache_avg:.6f},{improvement_percentage:.2f}\n")
            
            print(f"Summary benchmark created: {summary_file_path}")
            
        except (OSError, IOError, ValueError) as e:
            print(f"Error creating summary benchmark: {e}")
    
    def get_level_name(self):
        return f"level_{self.level_index + 1}"
    
    def get_step_name(self):
        if (not self.benchmark_matrix or 
            self.level_index >= len(self.benchmark_matrix) or 
            self.step_index >= len(self.benchmark_matrix[self.level_index])):
            return "unknown"
        screenshot_path = self.benchmark_matrix[self.level_index][self.step_index]
        return os.path.basename(screenshot_path).split('.')[0]

    def get_screenshot_path(self):
        return self.screenshot_path

    def load_current_level(self):
        if not self.benchmark_matrix:
            print("Error: No benchmark data available")
            return False
        if self.level_index >= len(self.benchmark_matrix):
            print("Error: Level index out of range")
            return False
        if self.step_index >= len(self.benchmark_matrix[self.level_index]):
            print("Error: Step index out of range")
            return False
        os.system(f'cp {self.benchmark_matrix[self.level_index][self.step_index]} {self.screenshot_path}')
        return True