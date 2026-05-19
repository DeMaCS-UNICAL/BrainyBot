import matplotlib.pyplot as plt
import time
from functools import cmp_to_key


import numpy as np
import random

def genetic_algorithm_tune_parameters(screenshot, parameters_lower_bound_dict, parameters_upper_bound_dict, process_function,  mutation_rate=0.1, crossover_rate=0.9,population_size=20,generation_no_improvements = 5,fitness_tolerance=0.05, path_image=None, show=False):
    parameter_names = list(parameters_lower_bound_dict.keys())
    num_parameters = len(parameter_names)
    
    bounds = [(parameters_lower_bound_dict[param], parameters_upper_bound_dict[param]) for param in parameter_names]

    def create_individual():
        return [int(random.uniform(low, high)) for low, high in bounds]
    
    def create_population():
        return [create_individual() for _ in range(population_size)]

    def fitness(individual):
        parameter_dict = dict(zip(parameter_names, individual))
        process_result = process_function(screenshot, parameter_dict)
        fitness = {"ratio":0,"objects_number":process_result["num_objects"],"types_number":process_result["num_groups"],"width_std":round(process_result["width_std"],3),"height_std":round(process_result["height_std"],3),"covered_area":process_result["covered_area"], "mean_width":process_result["mean_width"],"mean_height":process_result["mean_height"]}
        if process_result["num_groups"] > 0:
            fitness["ratio"]=process_result["num_objects"]/process_result["num_groups"]
        return fitness

    def dominates(a, b, eps):
        no_worse = (
            a["ratio"]         >= b["ratio"] *(1- eps["ratio"]) and
            a["covered_area"]  >= b["covered_area"]*(1  - eps["area"])  and
            a["width_std"]     <= b["width_std"] *(1+eps["std"])   and
            a["height_std"]    <= b["height_std"] *(1+ eps["std"])
        )
        strictly_better = (
            a["ratio"]         >  b["ratio"] or
            a["covered_area"]  >  b["covered_area"]  or
            a["width_std"]     <  b["width_std"]   or
            a["height_std"]    <  b["height_std"]
        )
        return no_worse and strictly_better

    def candidate_better_than(candidate, best):
        eps = {"ratio": 0.0, "area": fitness_tolerance, "std": fitness_tolerance}  
        return dominates(candidate, best, eps)
        
    def candidate_compare(a, b):
        fa, fb = a[1], b[1]
        if candidate_better_than(fa, fb): return -1
        if candidate_better_than(fb, fa): return  1
        return ( -1 if fa["ratio"] > fb["ratio"] else
                1 if fa["ratio"] < fa["ratio"] else 0 )

    def select_parents(population):
        tournament_size = 5
        selected_parents = []
        indexes = [i for i in range(len(population))]
        for _ in range(population_size // 2):
            tournament = random.sample(indexes, tournament_size)
            tournament.sort()  # Sort by fitness
            selected_parents.append(population[tournament[0]])  # Select the best individual
        return selected_parents

    def crossover(parent1, parent2):
        if random.random() < crossover_rate:
            crossover_point = random.randint(0, num_parameters-1)
            child1 = parent1[:crossover_point] + parent2[crossover_point:]
            child2 = parent2[:crossover_point] + parent1[crossover_point:]
            return child1, child2
        return parent1, parent2

    def mutate(individual):
        if random.random() < mutation_rate:
            param_index = random.randint(0, num_parameters - 1)
            low, high = bounds[param_index]
            individual[param_index] = int(random.uniform(low, high))
        return individual

    best_solution = None
    best_fitness_value = {}
    population = create_population()
    print("population created")
    no_improvements_since = 0
    generation = 0
    while True:
        population_fitness=[]
        start = time.time()
        generation += 1
        for i in range(len(population)):
            population_fitness.append(fitness(population[i]))

        sorted_population, sorted_fitness = zip(*sorted(zip(population, population_fitness), key=cmp_to_key(candidate_compare))) 
        population = list(sorted_population)
        population_fitness = list(sorted_fitness)
        if len(best_fitness_value.keys())==0 or candidate_better_than(population_fitness[0],best_fitness_value)>0:
            best_fitness_value = population_fitness[0]
            best_solution = population[0]
            no_improvements_since=0
        else:
            no_improvements_since += 1
            if no_improvements_since >= generation_no_improvements:
                break
        if show:
            print(f"Generation {generation }")
            print(f"Best Fitness: {best_fitness_value}")
            print(f"Best Params: {best_solution}")
            print(f"Worst Fitness: {population_fitness[-1]}")
            print(f"Worst Params: {population[-1]}")

        selected_parents = select_parents(population)
        evolution_start = time.time()
        next_generation = [best_solution]
        while len(next_generation)<population_size*2/3:
            parent1,parent2 = random.sample(selected_parents,2)
            child1, child2 = crossover(parent1, parent2)
            child1 = mutate(child1)
            child2 =mutate(child2)
            next_generation.append(child1)
            next_generation.append(child2)
        while len(next_generation)<population_size:
            next_generation.append(create_individual())
        population = next_generation

    parameter_dict = dict(zip(parameter_names, best_solution))
    
    if show:
        process_result = process_function(screenshot, parameter_dict, path_image, want_saving=True)
        print("going to show")
        print(parameter_dict)
        print("to achieve")
        print(best_fitness_value)
        print("#obj",process_result["num_objects"],"#types",process_result["num_groups"])
        plt.imshow(process_result["output_image"])
        plt.show()

    return parameter_dict, best_fitness_value["mean_width"],best_fitness_value["mean_height"], process_result["output_matches"]


