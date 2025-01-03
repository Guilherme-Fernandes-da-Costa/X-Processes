import plotting as plt
import recording as rec
import cycle as cyc
import initialpop as inp
import fitness as fit
import islands as isl
import multiprocessing as mlp
import datetime as dt
import log
from ast import literal_eval
from functools import partial
import petrinets as pn
import pytz
import argparse
import os

parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                 description= 'X-Processes is an automatic process model discovery method based on genetic algorithms',
                                 epilog='Example of use: python xprocesses.py -log input-logs/test.xes.gz -isl 4 -rnd 5 -gen 500 -tme 3600 -con 25 -fit 1 -prc 1 -gnl 1 -smp 1')

parser.add_argument('-log', required=True, type=str, help='log (default: None) | (type: .xes.gz)')
parser.add_argument('-isl', type=int, default=1, help='number of islands (default: 1) | (type: int)')
parser.add_argument('-rnd', type=int, default=1, help='number of rounds (default: 1) | (type: int)')
parser.add_argument('-gen', type=int, default=5000, help='stopping criterion - maximum number of generations (default: 5000) | (type: int)')
parser.add_argument('-tme', type=int, default=86400, help='stopping criterion - maximum execution time (default: 86400) | (type: int)')
parser.add_argument('-con', type=int, default=25, help='stopping criterion - convergence criterion, defined as the maximum consecutive number of generations with no fitness improvement for the best individual (default: 25) | (type: int)')
parser.add_argument('-fit', type=int, default=1, help='fitness weight (default: 1) | (type: int)')
parser.add_argument('-prc', type=int, default=1, help='precision weight (default: 1) | (type: int)')
parser.add_argument('-gnl', type=int, default=1, help='generalization weight (default: 1) | (type: int)')
parser.add_argument('-smp', type=int, default=1, help='simplicity weight (default: 1) | (type: int)')

args = parser.parse_args()

inputlog = args.log
number_of_islands = args.isl
number_of_rounds = args.rnd
max_number_of_generations = args.gen
max_processing_time = args.tme
stop_condition = args.con
fitness_weight = args.fit
precision_weight = args.prc
generalization_weight = args.gnl
simplicity_weight = args.smp


def run_round(paramenter_set, number_of_islands, round, broadcast, messenger, island_sizes, percentage_of_best_individuals_for_migration_all_islands, algo_option, algo_option_changed, full_log, alphabet, log_name, xes_log, max_number_of_generations, max_processing_time, stop_condition, bestone_file, island_number):
    island_start = dt.datetime.now()
    population_size = int(paramenter_set[island_number + 1][0])
    migration_time = int(paramenter_set[island_number + 1][1])
    percentage_of_best_individuals_for_migration_per_island = float(paramenter_set[island_number + 1][2])
    percentage_of_individuals_for_migration_per_island = float(paramenter_set[island_number + 1][3])
    max_perc_of_num_tasks_for_crossover = float(paramenter_set[island_number + 1][4])
    crossover_probability = float(paramenter_set[island_number + 1][5])
    task_mutation_probability = float(paramenter_set[island_number + 1][6])
    gateway_mutation_probability = float(paramenter_set[island_number + 1][7])
    max_perc_of_num_tasks_for_task_mutation = float(paramenter_set[island_number + 1][8])
    max_perc_of_num_tasks_for_gateway_mutation = float(paramenter_set[island_number + 1][9])
    elitism_percentage = float(paramenter_set[island_number + 1][10])
    island_sizes[island_number] = population_size
    percentage_of_best_individuals_for_migration_all_islands[island_number] = percentage_of_best_individuals_for_migration_per_island
    (population, evaluated_population, reference_cromossome, average_enabled_tasks) = inp.initialize_population(population_size, alphabet, full_log, xes_log, algo_option[0], fitness_weight, precision_weight, generalization_weight, simplicity_weight)

    fitness_evolution = []                                                                                              
    (highest_value_and_position, sorted_evaluated_population) = cyc.choose_highest(evaluated_population)                
    lowest_value = cyc.choose_lowest(sorted_evaluated_population)                                                       
    average_value = cyc.calculate_average(evaluated_population)                                                         
    fitness_evolution.append([lowest_value, highest_value_and_position[0][0], average_value, 0, highest_value_and_position[0][1], highest_value_and_position[0][2], highest_value_and_position[0][3], highest_value_and_position[0][4], 0, 0, 0, 0])     
    pn.create_pn(population[highest_value_and_position[1]], alphabet, island_number, 0 , log_name, 0)
    island_end = dt.datetime.now()                                                                                      
    island_duration = island_end - island_start                                                                         
    print('r', round, '%.5f' % highest_value_and_position[0][0], '%.5f' % highest_value_and_position[0][1], '%.5f' % highest_value_and_position[0][2], '%.5f' % highest_value_and_position[0][3], '%.5f' % highest_value_and_position[0][4], '| i', '{:>2}'.format(island_number), '| g', '{:>3}'.format('0'), '| REP', '{:>2}'.format(fitness_evolution[0][8]), '{:>2}'.format(fitness_evolution[0][3]), '{:>2}'.format(fitness_evolution[0][9]), '{:>2}'.format(fitness_evolution[0][10]), '{:>2}'.format(fitness_evolution[0][11]), '|', island_duration, '|', dt.datetime.now(pytz.timezone("Brazil/East")).strftime("%H:%M:%S"), '|', algo_option[0])     

    isl.set_broadcast(population, sorted_evaluated_population, island_number, percentage_of_best_individuals_for_migration_per_island, broadcast)  
    if isl.receive_individuals(population, island_number, sorted_evaluated_population, messenger, evaluated_population) == 1:  
        (highest_value_and_position, sorted_evaluated_population) = cyc.choose_highest(evaluated_population)  
    if (migration_time == 1):  
        island_fitness = []  
        for i in range(len(evaluated_population[1])):  
            island_fitness.append(evaluated_population[1][i][0])  
        isl.do_migration(population, island_number, number_of_islands, island_fitness, percentage_of_individuals_for_migration_per_island, broadcast, island_sizes, percentage_of_best_individuals_for_migration_all_islands, evaluated_population)  
        isl.send_individuals(population, island_number, number_of_islands, sorted_evaluated_population, messenger)  
        (highest_value_and_position, sorted_evaluated_population) = cyc.choose_highest(evaluated_population)  

    rec.record_evolution(log_name, str(round), paramenter_set[island_number + 1], island_number, highest_value_and_position[0], fitness_evolution, alphabet, population[highest_value_and_position[1]], island_start, island_end, island_duration, 0, algo_option[0])  
    for current_generation in range(1, max_number_of_generations):                                                          
        (population, evaluated_population) = cyc.generation(population, reference_cromossome, evaluated_population, crossover_probability, max_perc_of_num_tasks_for_crossover, task_mutation_probability, gateway_mutation_probability, max_perc_of_num_tasks_for_task_mutation, max_perc_of_num_tasks_for_gateway_mutation, elitism_percentage, sorted_evaluated_population, alphabet, xes_log, algo_option[0], fitness_weight, precision_weight, generalization_weight, simplicity_weight)
        (highest_value_and_position, sorted_evaluated_population) = cyc.choose_highest(evaluated_population)
        lowest_value = cyc.choose_lowest(sorted_evaluated_population)                                                   
        average_value = cyc.calculate_average(evaluated_population)                                                     
        fitness_evolution.append([lowest_value, highest_value_and_position[0][0], average_value, 0, highest_value_and_position[0][1], highest_value_and_position[0][2], highest_value_and_position[0][3], highest_value_and_position[0][4], 0, 0, 0, 0])     
        if fitness_evolution[current_generation][1] == fitness_evolution[current_generation - 1][1]:                    
            fitness_evolution[current_generation][8] = fitness_evolution[current_generation - 1][8] + 1                 
        else:                                                                                                           
             if fitness_evolution[current_generation][1] < fitness_evolution[current_generation - 1][1]:                
                fitness_evolution[current_generation][8] = -1                                                           
        if fitness_evolution[current_generation][4] == fitness_evolution[current_generation - 1][4]:                    
            fitness_evolution[current_generation][3] = fitness_evolution[current_generation - 1][3] + 1                 
        else:                                                                                                           
            if fitness_evolution[current_generation][4] < fitness_evolution[current_generation - 1][4]:                 
                fitness_evolution[current_generation][3] = -1                                                           
        if fitness_evolution[current_generation][5] == fitness_evolution[current_generation - 1][5]:                    
            fitness_evolution[current_generation][9] = fitness_evolution[current_generation - 1][9] + 1                 
        else:                                                                                                           
            if fitness_evolution[current_generation][5] < fitness_evolution[current_generation - 1][5]:                 
                fitness_evolution[current_generation][9] = -1                                                           
        if fitness_evolution[current_generation][6] == fitness_evolution[current_generation - 1][6]:                    
            fitness_evolution[current_generation][10] = fitness_evolution[current_generation - 1][10] + 1               
        else:                                                                                                           
            if fitness_evolution[current_generation][6] < fitness_evolution[current_generation - 1][6]:                 
                fitness_evolution[current_generation][10] = -1                                                          
        if fitness_evolution[current_generation][7] == fitness_evolution[current_generation - 1][7]:                    
            fitness_evolution[current_generation][11] = fitness_evolution[current_generation - 1][11] + 1               
        else:                                                                                                           
            if fitness_evolution[current_generation][7] < fitness_evolution[current_generation - 1][7]:                 
                fitness_evolution[current_generation][11] = -1                                                          
        pn.create_pn(population[highest_value_and_position[1]], alphabet, island_number, current_generation, log_name, round)
        island_end = dt.datetime.now()                                                                                  
        island_duration = island_end - island_start                                                                     
        print('r', round, '%.5f' % highest_value_and_position[0][0], '%.5f' % highest_value_and_position[0][1], '%.5f' % highest_value_and_position[0][2], '%.5f' % highest_value_and_position[0][3], '%.5f' % highest_value_and_position[0][4], '| i', '{:>2}'.format(island_number), '| g', '{:>3}'.format(current_generation), '| REP', '{:>2}'.format(fitness_evolution[current_generation][8]), '{:>2}'.format(fitness_evolution[current_generation][3]), '{:>2}'.format(fitness_evolution[current_generation][9]), '{:>2}'.format(fitness_evolution[current_generation][10]), '{:>2}'.format(fitness_evolution[current_generation][11]), '|', island_duration, '|', dt.datetime.now(pytz.timezone("Brazil/East")).strftime("%H:%M:%S"), '|', algo_option[0])     
        isl.set_broadcast(population, sorted_evaluated_population, island_number, percentage_of_best_individuals_for_migration_per_island, broadcast)     
        if ((fitness_evolution[current_generation][8] >= stop_condition)) or (island_duration > dt.timedelta(seconds=max_processing_time)):     
            break                                                                                                       
        if isl.receive_individuals(population, island_number, sorted_evaluated_population, messenger, evaluated_population) == 1:             
            (highest_value_and_position, sorted_evaluated_population) = cyc.choose_highest(evaluated_population)        
        if (current_generation > 0) and (current_generation % migration_time == 0):                                     
            island_fitness = []                                                                                         
            for i in range(len(evaluated_population[1])):                                                               
                island_fitness.append(evaluated_population[1][i][0])                                                    
            isl.do_migration(population, island_number, number_of_islands, island_fitness, percentage_of_individuals_for_migration_per_island, broadcast, island_sizes, percentage_of_best_individuals_for_migration_all_islands, evaluated_population)     
            isl.send_individuals(population, island_number, number_of_islands, sorted_evaluated_population, messenger)  
            (highest_value_and_position, sorted_evaluated_population) = cyc.choose_highest(evaluated_population)        
        rec.record_evolution(log_name, str(round), paramenter_set[island_number + 1], island_number, highest_value_and_position[0], fitness_evolution, alphabet, population[highest_value_and_position[1]], island_start, island_end, island_duration, current_generation, algo_option[0])     
        if (algo_option[0] != 'ALIGNMENT_BASED-ETCONFORMANCE_TOKEN') and (fitness_evolution[current_generation][8] >= (stop_condition * 2 / 5)):
                algo_option[0] = 'ALIGNMENT_BASED-ETCONFORMANCE_TOKEN'
        if (algo_option[0] == 'ALIGNMENT_BASED-ETCONFORMANCE_TOKEN') and (algo_option_changed[island_number] == 0):
            evaluated_population = fit.evaluate_population(population, alphabet, xes_log, algo_option[0], fitness_weight, precision_weight, generalization_weight, simplicity_weight)
            (highest_value_and_position, sorted_evaluated_population) = cyc.choose_highest(evaluated_population)
            for island_n in range(0, number_of_islands):
                isl.set_broadcast_null(island_n, broadcast)  
                isl.send_individuals_null(island_n, messenger)  
            algo_option_changed[island_number] = 1
    evaluated_final_population = fit.evaluate_population(population, alphabet, xes_log, 'ALIGNMENT_BASED-ALIGN_ETCONFORMANCE', fitness_weight, precision_weight, generalization_weight, simplicity_weight)
    (highest_value_and_position, sorted_evaluated_population) = cyc.choose_highest(evaluated_final_population)
    lowest_value = cyc.choose_lowest(sorted_evaluated_population)  
    average_value = cyc.calculate_average(evaluated_population)
    fitness_evolution.append([lowest_value, highest_value_and_position[0][0], average_value, 0, highest_value_and_position[0][1], highest_value_and_position[0][2], highest_value_and_position[0][3], highest_value_and_position[0][4], 0, 0, 0, 0])
    print('r', round, '%.5f' % highest_value_and_position[0][0], '%.5f' % highest_value_and_position[0][1], '%.5f' % highest_value_and_position[0][2], '%.5f' % highest_value_and_position[0][3], '%.5f' % highest_value_and_position[0][4], '| i', '{:>2}'.format(island_number), '| g', '{:>3}'.format(current_generation), '| REP', '{:>2}'.format(fitness_evolution[current_generation][8]), '{:>2}'.format(fitness_evolution[current_generation][3]), '{:>2}'.format(fitness_evolution[current_generation][9]), '{:>2}'.format(fitness_evolution[current_generation][10]), '{:>2}'.format(fitness_evolution[current_generation][11]), '|', island_duration, '|', dt.datetime.now(pytz.timezone("Brazil/East")).strftime("%H:%M:%S"), '|', 'ALIGNMENT_BASED-ALIGN_ETCONFORMANCE')
    plt.plot_evolution_per_island(fitness_evolution, log_name, str(round), island_number)
    previous_plotting = []                                                                                              
    with open('output-graphs/plotting/plotting_{0}.txt'.format(island_number), 'r') as plott:                           
        for line in isl.nonblank_lines(plott):                                                                          
            previous_plotting.append(literal_eval(line))                                                                
        plott.close()                                                                                                       
    previous_plotting.extend(fitness_evolution)                                                                         
    with open('output-graphs/plotting/plotting_{0}.txt'.format(island_number), 'w') as plott:                           
        for ini in range(len(previous_plotting)):                                                                       
            plott.write(str(previous_plotting[ini]) + '\n')                                                             
        plott.close()                                                                                                       
    rec.record_evolution(log_name, str(round), paramenter_set[island_number + 1], island_number, highest_value_and_position[0], fitness_evolution, alphabet, population[highest_value_and_position[1]], island_start, island_end, island_duration, current_generation, 'ALIGNMENT_BASED-ALIGN_ETCONFORMANCE')
    print('Final results ==>', 'r', round, '| ISL:', island_number, '| ISL-DURATION:', island_duration, '| r', round, '| HM:', '%.5f' % highest_value_and_position[0][0], '| FIT:', '%.5f' % highest_value_and_position[0][1], '| PREC:', '%.5f' % highest_value_and_position[0][2], '| GEN:', '%.5f' % highest_value_and_position[0][3], '| SIMP:', '%.5f' % highest_value_and_position[0][4], '| ALPHABET:', alphabet, '| BEST INDIVIDUAL:', population[highest_value_and_position[1]])
    rec.record_bestone(island_number, highest_value_and_position[0][0], current_generation, bestone_file)
    return


if __name__ == '__main__':
        for round in range(0, number_of_rounds):
            paramenter_set = []
            alphabet = []
            island_ids = []
            with open('input-parameters/input-parameters.csv', 'r') as parameters:
                for line in isl.nonblank_lines(parameters):
                    paramenter_set.append(line.split(';'))
                parameters.close()
            full_log, log_name, xes_log = log.import_log(inputlog)
            bestone_file = 'petri-nets/' + log_name.replace("\\", "-") + '.txt'
            if os.path.exists(bestone_file):
                os.remove(bestone_file)
            inp.create_alphabet(full_log, alphabet)
            inp.process_log(full_log)
            for island in range(number_of_islands):                                                                         
                island_ids.append(island)                                                                                   
            isl.create_plotting_files(island_ids, number_of_islands)                                                        
            p = mlp.Pool(number_of_islands)                                                                                 
            m = mlp.Manager()                                                                                               
            broadcast = m.list()                                                                                            
            messenger = m.list()                                                                                            
            island_sizes = m.list()                                                                                         
            percentage_of_best_individuals_for_migration_all_islands = m.list()                                             
            algo_option = m.list()
            algo_option_changed = m.list()
            func = partial(run_round, paramenter_set, number_of_islands)                                                    
            for island in range(number_of_islands):                                                                         
                broadcast.append([])                                                                                        
                messenger.append([[],[],[]])                                                                                
                island_sizes.append(0)                                                                                      
                percentage_of_best_individuals_for_migration_all_islands.append(0)                                          
                algo_option_changed.append(0)
            broadcast.append(1)                                                                                             
            algo_option.append('TOKEN_BASED-ETCONFORMANCE_TOKEN')
            func2 = partial(func, round, broadcast, messenger, island_sizes, percentage_of_best_individuals_for_migration_all_islands, algo_option, algo_option_changed, full_log, alphabet, log_name, xes_log, max_number_of_generations, max_processing_time, stop_condition, bestone_file)
            p.map(func2, island_ids)
            plt.plot_evolution_integrated(log_name, str(round), number_of_islands)
            with open(bestone_file, 'r') as bestone:
                best_island_number = bestone.readline().strip()
                best_highest_hm = bestone.readline().strip()
                generation_best = bestone.readline().strip()
                bestone.close()
            print('Best island: ', best_island_number)
            print('Highest HM: ', best_highest_hm)
            print('Generation: ', generation_best)
            pn.write_and_show_best_pn(best_island_number, log_name, round, generation_best)
            p.close()