import random as ran
import numpy as np
import copy
from numba import njit, prange
from concurrent.futures import ThreadPoolExecutor

def parent_selection(evaluated_population):
    pop_size = len(evaluated_population[1])
    opponent_1, opponent_2 = ran.sample(range(pop_size), 2)
    o1_values = evaluated_population[1][opponent_1]
    o2_values = evaluated_population[1][opponent_2]
    if o1_values[0] > o2_values[0]:
        return opponent_1
    elif o1_values[0] < o2_values[0]:
        return opponent_2
    else:
        if o1_values[4] > o2_values[4]:
            return opponent_1
        elif o1_values[4] < o2_values[4]:
            return opponent_2
        else:
            return opponent_1 if o1_values[3] >= o2_values[3] else opponent_2

def crossover_per_process(crossover_probability, max_perc_of_num_tasks_for_crossover, cromossome_1, cromossome_2):
    if ran.random() < crossover_probability:
        max_length = len(cromossome_1) - 1
        max_number_of_tasks = 1 if max_perc_of_num_tasks_for_crossover == -1 else max(1, int(max_perc_of_num_tasks_for_crossover * max_length))
        number_of_tasks = ran.randint(1, max_number_of_tasks + 1)
        offspring_1, offspring_2 = np.copy(cromossome_1), np.copy(cromossome_2)

        def swap_task(i):
            chosen_task = int(ran.random() * max_length)
            crossover_level = ran.random()
            if crossover_level < 1 / 3 or crossover_level > 2 / 3:
                offspring_1[chosen_task] = cromossome_2[chosen_task]
                offspring_2[chosen_task] = cromossome_1[chosen_task]
            if crossover_level >= 1 / 3:
                for j in range(len(offspring_1)):
                    offspring_1[j][chosen_task] = cromossome_2[j][chosen_task]
                    offspring_2[j][chosen_task] = cromossome_1[j][chosen_task]

        for i in range(number_of_tasks):
            swap_task(i)

        adjust_produced_consumed_tokens(offspring_1)
        adjust_produced_consumed_tokens(offspring_2)

        @njit
        def check_active_tasks(offspring):
            for raw in range(len(offspring) - 2):
                if not is_there_at_least_one_raw_active_task(offspring, raw):
                    return False
                elif not is_there_at_least_two_raw_active_tasks(offspring, raw) and offspring[raw][-1] != 0:
                    offspring[raw][-1] = 0
                elif is_there_at_least_two_raw_active_tasks(offspring, raw) and offspring[raw][-1] == 0:
                    offspring[raw][-1] = np.random.randint(1, 4)
            for col in range(1, len(offspring) - 1):
                if not is_there_at_least_one_column_active_task(offspring, col):
                    return False
                elif (not is_there_at_least_two_column_active_tasks(offspring, col) and offspring[-1][col] != 0):
                    offspring[-1][col] = 0
                elif is_there_at_least_two_column_active_tasks(offspring, col) and offspring[-1][col] == 0:
                    offspring[-1][col] = np.random.randint(1, 4)
            return True

        checks = [check_active_tasks(offspring_1), check_active_tasks(offspring_2)]
        if all(checks):
            return offspring_2, offspring_1
    return cromossome_1, cromossome_2

def mutation(cromossome, task_mutation_probability, gateway_mutation_probability, max_perc_of_num_tasks_for_task_mutation, max_perc_of_num_tasks_for_gateway_mutation, reference_cromossome):
    if ran.random() < task_mutation_probability:
        task_mutation(cromossome, max_perc_of_num_tasks_for_task_mutation, reference_cromossome)
    if ran.random() < gateway_mutation_probability:
        gateway_mutation(cromossome, max_perc_of_num_tasks_for_gateway_mutation)

@njit
def mutate_task(cromossome, chosen_task, reference_cromossome, reverse=False):
    cromossome_len = len(cromossome)
    if reverse:
        if chosen_task == len(cromossome) - 2:
            return
        for j in range(cromossome_len):
            new_output = int(ran.random() * (cromossome_len - 1))
            if reference_cromossome[chosen_task][new_output] == 1:
                break
        cromossome[chosen_task][new_output] ^= 1
        if cromossome[chosen_task][new_output] == 0:
            chosen_task2 = mutate_and_choose(cromossome, reference_cromossome, chosen_task, new_output)
            cromossome[chosen_task2][new_output] = 1
            if not is_there_at_least_two_raw_active_tasks(cromossome, chosen_task2) and cromossome[chosen_task2][-1] != 0:
                cromossome[chosen_task2][-1] = 0
            elif is_there_at_least_two_raw_active_tasks(cromossome, chosen_task2) and cromossome[chosen_task2][-1] == 0:
                cromossome[chosen_task2][-1] = np.random.randint(1, 4)
        if not is_there_at_least_two_raw_active_tasks(cromossome, chosen_task) and cromossome[chosen_task][-1] != 0:
            cromossome[chosen_task][-1] = 0
        elif is_there_at_least_two_raw_active_tasks(cromossome, chosen_task) and cromossome[chosen_task][-1] == 0:
            cromossome[chosen_task][-1] = np.random.randint(1, 4)
        if (not is_there_at_least_two_column_active_tasks(cromossome, new_output) and cromossome[-1][new_output] != 0):
            cromossome[-1][new_output] = 0
        elif is_there_at_least_two_column_active_tasks(cromossome, new_output) and cromossome[-1][new_output] == 0:
            cromossome[-1][new_output] = np.random.randint(1, 4)
    else:
        if chosen_task == 0:
            return
        for j in range(cromossome_len):
            new_input = int(ran.random() * (cromossome_len - 1))
            if reference_cromossome[new_input][chosen_task] == 1:
                break
        cromossome[new_input][chosen_task] ^= 1
        if cromossome[new_input][chosen_task] == 0:
            chosen_task2 = mutate_and_choose(cromossome, reference_cromossome, new_input, chosen_task)
            cromossome[new_input][chosen_task2] = 1
            if (not is_there_at_least_two_column_active_tasks(cromossome, chosen_task2) and cromossome[-1][chosen_task2] != 0):
                cromossome[-1][chosen_task2] = 0
            elif is_there_at_least_two_column_active_tasks(cromossome, chosen_task2) and cromossome[-1][chosen_task2] == 0:
                cromossome[-1][chosen_task2] = np.random.randint(1, 4)
        if not is_there_at_least_two_raw_active_tasks(cromossome, new_input) and cromossome[new_input][-1] != 0:
            cromossome[new_input][-1] = 0
        elif is_there_at_least_two_raw_active_tasks(cromossome, new_input) and cromossome[new_input][-1] == 0:
            cromossome[new_input][-1] = np.random.randint(1, 4)
        if (not is_there_at_least_two_column_active_tasks(cromossome, chosen_task) and cromossome[-1][chosen_task] != 0):
            cromossome[-1][chosen_task] = 0
        elif is_there_at_least_two_column_active_tasks(cromossome, chosen_task) and cromossome[-1][chosen_task] == 0:
            cromossome[-1][chosen_task] = np.random.randint(1, 4)

@njit
def mutate_and_choose(cromossome, reference_cromossome, val1, val2):
    cromossome_len = len(cromossome)
    for k in range(1, cromossome_len - 1):
        if cromossome[val1][k] == 1:
            return val1
    chosen_task2 = int(ran.random() * (cromossome_len - 1))
    count = 0
    while (chosen_task2 == val1) or (chosen_task2 == val2) or (reference_cromossome[val1][chosen_task2] == 0):
        chosen_task2 = int(ran.random() * (cromossome_len - 1))
        count += 1
        if count > (cromossome_len * 0.25):
            return val1
    return chosen_task2

def adjust_produced_consumed_tokens(cromossome):
    single_consumed = count_consumed_single_tokens(cromossome)
    single_produced = count_produced_single_tokens(cromossome)
    XOR_consumed = count_consumed_XOR_tokens(cromossome)
    XOR_produced = count_produced_XOR_tokens(cromossome)
    AND_consumed = count_consumed_AND_tokens(cromossome)
    AND_produced = count_produced_AND_tokens(cromossome)
    OR_consumed = count_consumed_OR_tokens(cromossome)
    OR_produced = count_produced_OR_tokens(cromossome)

    # if (single_consumed != single_produced) or (XOR_consumed != XOR_produced) or (AND_consumed != AND_produced) or (OR_consumed != OR_produced):
    #     if (single_produced + XOR_produced + AND_produced + OR_produced) > (single_consumed + XOR_consumed + AND_consumed + OR_consumed):
    #         increase_number_of_consumed_tokens(cromossome, XOR_produced, AND_produced, OR_produced)
    #     else:
    #         increase_number_of_produced_tokens(cromossome, XOR_consumed, AND_consumed, OR_consumed)
    if (single_produced + XOR_produced + AND_produced + OR_produced) > (single_consumed + XOR_consumed + AND_consumed + OR_consumed):
         increase_number_of_consumed_tokens(cromossome, XOR_produced, AND_produced, OR_produced)
    elif (single_produced + XOR_produced + AND_produced + OR_produced) < (single_consumed + XOR_consumed + AND_consumed + OR_consumed):
        increase_number_of_produced_tokens(cromossome, XOR_consumed, AND_consumed, OR_consumed)

def task_mutation(cromossome, max_perc_of_num_tasks_for_task_mutation, reference_cromossome):
    cromossome_len = len(cromossome)
    max_number_of_tasks = 1 if max_perc_of_num_tasks_for_task_mutation == -1 else max(1, int(max_perc_of_num_tasks_for_task_mutation * (cromossome_len - 1)))
    while True:
        temp_cromossome = np.copy(cromossome)
        unreachableOrNoProperEndTask = True
        number_of_tasks = ran.randint(1, max_number_of_tasks)
        for _ in range(number_of_tasks):
            chosen_task = int(ran.random() * (cromossome_len - 1))
            chosen_mutation_type = ran.random()
            mutate_task(cromossome, chosen_task, reference_cromossome, reverse=(chosen_mutation_type >= 1 / 2))
            adjust_produced_consumed_tokens(cromossome)
        for n in range(cromossome_len - 2):
            if not is_there_at_least_one_raw_active_task(cromossome, n):
                unreachableOrNoProperEndTask = False
                break
        if unreachableOrNoProperEndTask:
            for n in range(1, cromossome_len - 1):
                if not is_there_at_least_one_column_active_task(cromossome, n):
                    unreachableOrNoProperEndTask = False
                    break
        if unreachableOrNoProperEndTask:
            return
        cromossome = temp_cromossome

def gateway_mutation(cromossome, max_perc_of_num_tasks_for_gateway_mutation):
    len_cromossome = len(cromossome)
    if max_perc_of_num_tasks_for_gateway_mutation == -1:
        number_of_tasks = 1
    else:
        max_number_of_tasks = max(1, int(max_perc_of_num_tasks_for_gateway_mutation * (len_cromossome - 1)))
        number_of_tasks = ran.randint(1, max_number_of_tasks)
    for _ in range(number_of_tasks):
        mutate_and_adjust(cromossome, len_cromossome)

def mutate_and_adjust(cromossome, len_cromossome):
    gateway_mutation_core(cromossome, len_cromossome)
    adjust_produced_consumed_tokens(cromossome)

@njit
def gateway_mutation_core(cromossome, len_cromossome):
    valid_rows = []
    valid_columns = []
    for i in range(len_cromossome - 2):
        if cromossome[i][-1] in [1, 2, 3]:
            valid_rows.append(i)
    for j in range(1, len_cromossome - 1):
        if cromossome[-1][j] in [1, 2, 3]:
            valid_columns.append(j)
    valid_rows = np.array(valid_rows)
    valid_columns = np.array(valid_columns)
    if len(valid_rows) == 0 and len(valid_columns) == 0:
        return
    chosen_operator_position = ran.random()
    if len(valid_rows) > 0 and len(valid_columns) > 0:
        if chosen_operator_position < 1 / 2:
            chosen_task = valid_rows[int(np.random.randint(len(valid_rows)))]
            element = cromossome[chosen_task][-1]
        else:
            chosen_task = valid_columns[int(np.random.randint(len(valid_columns)))]
            element = cromossome[-1][chosen_task]
    elif len(valid_rows) > 0:
        chosen_task = valid_rows[int(np.random.randint(len(valid_rows)))]
        element = cromossome[chosen_task][-1]
    else:
        chosen_task = valid_columns[int(np.random.randint(len(valid_columns)))]
        element = cromossome[-1][chosen_task]
    if element == 1:
        new_value = 2 if np.random.random() < 0.5 else 3
    elif element == 2:
        new_value = 1 if np.random.random() < 0.5 else 3
    elif element == 3:
        new_value = 1 if np.random.random() < 0.5 else 2
    if chosen_operator_position < 1 / 2:
        cromossome[chosen_task][-1] = new_value
    else:
        cromossome[-1][chosen_task] = new_value

@njit
def count_produced_single_tokens(cromossome):
    number_of_produced_single_tokens = 0
    for i in range(len(cromossome) - 2):
        if cromossome[i][-1] == 0:
            number_of_produced_single_tokens += 1
    return number_of_produced_single_tokens

@njit
def count_consumed_single_tokens(cromossome):
    number_of_consumed_single_tokens = 0
    for i in range(1, len(cromossome) - 1):
        if cromossome[-1][i] == 0:
            number_of_consumed_single_tokens += 1
    return number_of_consumed_single_tokens

@njit
def count_produced_XOR_tokens(cromossome):
    number_of_produced_XOR_tokens = 0
    for i in range(len(cromossome) - 2):
        if cromossome[i][-1] == 1:
            number_of_produced_XOR_tokens += 1
    return number_of_produced_XOR_tokens

@njit
def count_consumed_XOR_tokens(cromossome):
    number_of_consumed_XOR_tokens = 0
    for i in range(1, len(cromossome) - 1):
        if cromossome[-1][i] == 1:
            number_of_consumed_XOR_tokens += 1
    return number_of_consumed_XOR_tokens

@njit
def count_produced_AND_tokens(cromossome):
    number_of_produced_AND_tokens = 0
    for i in range(len(cromossome) - 2):
        if cromossome[i][-1] == 2:
            for j in range(1, len(cromossome[i]) - 1):
                number_of_produced_AND_tokens += cromossome[i][j]
    return number_of_produced_AND_tokens

@njit
def count_consumed_AND_tokens(cromossome):
    number_of_consumed_AND_tokens = 0
    for i in range(1, len(cromossome) - 1):
        if cromossome[-1][i] == 2:
            for j in range(len(cromossome[i]) - 2):
                number_of_consumed_AND_tokens += + cromossome[j][i]
    return number_of_consumed_AND_tokens

@njit
def count_produced_OR_tokens(cromossome):
    number_of_produced_OR_tokens = 0
    for i in range(len(cromossome) - 2):
        if cromossome[i][-1] == 3:
            for j in range(1, len(cromossome[i]) - 1):
                number_of_produced_OR_tokens += cromossome[i][j]
    return number_of_produced_OR_tokens

@njit
def count_consumed_OR_tokens(cromossome):
    number_of_consumed_OR_tokens = 0
    for i in range(1, len(cromossome) - 1):
        if cromossome[-1][i] == 3:
            for j in range(len(cromossome[i]) - 2):
                number_of_consumed_OR_tokens += + cromossome[j][i]
    return number_of_consumed_OR_tokens

@njit
def increase_number_of_produced_tokens(cromossome, number_of_consumed_XOR_tokens, number_of_consumed_AND_tokens, number_of_consumed_OR_tokens):
    n = len(cromossome)
    copy_of_output_gateways = np.array([task[-1] for task in cromossome])
    number_of_attempts = int(n * 0.5)
    for i in range(number_of_attempts):
        chosen_task = np.random.randint(0, n - 2)
        max_i = 0
        while (cromossome[chosen_task][-1] == 2 or cromossome[chosen_task][-1] == 3) and max_i <= n:
            max_i += 1
            chosen_task = np.random.randint(0, n - 2)
        if max_i <= n:
            if cromossome[chosen_task][-1] == 1:
                if np.random.rand() < 0.5:
                    cromossome[chosen_task][-1] = 2
                else:
                    cromossome[chosen_task][-1] = 3
        number_of_produced_XOR_tokens = count_produced_XOR_tokens(cromossome)
        number_of_produced_AND_tokens = count_produced_AND_tokens(cromossome)
        number_of_produced_OR_tokens = count_produced_OR_tokens(cromossome)
        max_i = 0
        while not ((number_of_consumed_XOR_tokens == number_of_produced_XOR_tokens) and (number_of_consumed_AND_tokens == number_of_produced_AND_tokens) and (number_of_consumed_OR_tokens == number_of_produced_OR_tokens)) and max_i <= n:
            max_i += 1
            chosen_task = np.random.randint(0, n - 2)
            max_j = 0
            while (cromossome[chosen_task][-1] == 2 or cromossome[chosen_task][-1] == 3) and max_j <= n:
                max_j += 1
                chosen_task = np.random.randint(0, n - 2)
            if max_j <= n:
                if cromossome[chosen_task][-1] == 1:
                    if np.random.rand() < 0.5:
                        cromossome[chosen_task][-1] = 2
                    else:
                        cromossome[chosen_task][-1] = 3
                    number_of_produced_XOR_tokens = count_produced_XOR_tokens(cromossome)
                    number_of_produced_AND_tokens = count_produced_AND_tokens(cromossome)
                    number_of_produced_OR_tokens = count_produced_OR_tokens(cromossome)
        if (number_of_consumed_XOR_tokens != number_of_produced_XOR_tokens) or (number_of_consumed_AND_tokens != number_of_produced_AND_tokens) or (number_of_consumed_OR_tokens != number_of_produced_OR_tokens):
            cromossome[:, -1] = copy_of_output_gateways
    if i == number_of_attempts - 1:
        decrease_number_of_consumed_tokens(cromossome, count_produced_XOR_tokens(cromossome), count_produced_AND_tokens(cromossome), count_produced_OR_tokens(cromossome))

@njit
def increase_number_of_consumed_tokens(cromossome, number_of_produced_XOR_tokens, number_of_produced_AND_tokens, number_of_produced_OR_tokens):
    n = len(cromossome)
    copy_of_input_gateways = cromossome[-1].copy()
    number_of_attempts = int(n * 0.5)
    for i in range(number_of_attempts):
        chosen_task = np.random.randint(1, n - 1)
        max_i = 0
        while (cromossome[-1][chosen_task] == 2 or cromossome[-1][chosen_task] == 3) and max_i <= n:
            max_i += 1
            chosen_task = np.random.randint(1, n - 1)
        if max_i <= n:
            if cromossome[-1][chosen_task] == 1:
                if np.random.rand() < 0.5:
                    cromossome[-1][chosen_task] = 2
                else:
                    cromossome[-1][chosen_task] = 3
        number_of_consumed_XOR_tokens = count_consumed_XOR_tokens(cromossome)
        number_of_consumed_AND_tokens = count_consumed_AND_tokens(cromossome)
        number_of_consumed_OR_tokens = count_consumed_OR_tokens(cromossome)
        max_i = 0
        while not ((number_of_consumed_XOR_tokens == number_of_produced_XOR_tokens) and (number_of_consumed_AND_tokens == number_of_produced_AND_tokens) and (number_of_consumed_OR_tokens == number_of_produced_OR_tokens)) and max_i <= n:
            max_i += 1
            chosen_task = np.random.randint(1, n - 1)
            max_j = 0
            while (cromossome[-1][chosen_task] == 2 or cromossome[-1][chosen_task] == 3) and max_j <= n:
                max_j += 1
                chosen_task = np.random.randint(1, n - 1)
            if max_j <= n:
                if cromossome[-1][chosen_task] == 1:
                    if np.random.rand() < 0.5:
                        cromossome[-1][chosen_task] = 2
                    else:
                        cromossome[-1][chosen_task] = 3
                    number_of_consumed_XOR_tokens = count_consumed_XOR_tokens(cromossome)
                    number_of_consumed_AND_tokens = count_consumed_AND_tokens(cromossome)
                    number_of_consumed_OR_tokens = count_consumed_OR_tokens(cromossome)
        if (number_of_consumed_XOR_tokens != number_of_produced_XOR_tokens) or (number_of_consumed_AND_tokens != number_of_produced_AND_tokens) or (number_of_consumed_OR_tokens != number_of_produced_OR_tokens):
            cromossome[-1] = copy_of_input_gateways.copy()
    if i == number_of_attempts - 1:
        decrease_number_of_produced_tokens(cromossome, count_consumed_XOR_tokens(cromossome), count_consumed_AND_tokens(cromossome), count_consumed_OR_tokens(cromossome))

@njit
def decrease_number_of_produced_tokens(cromossome, number_of_consumed_XOR_tokens, number_of_consumed_AND_tokens, number_of_consumed_OR_tokens):
    n = len(cromossome)
    copy_of_output_gateways = np.array([task[-1] for task in cromossome])
    number_of_attempts = int(n * 0.5)
    for i in range(number_of_attempts):
        chosen_task = np.random.randint(0, n - 2)
        max_i = 0
        while (cromossome[chosen_task][-1] == 0 or cromossome[chosen_task][-1] == 1) and max_i <= n:
            max_i += 1
            chosen_task = np.random.randint(0, n - 2)
        if max_i <= n:
            cromossome[chosen_task][-1] = 1
        number_of_produced_XOR_tokens = count_produced_XOR_tokens(cromossome)
        number_of_produced_AND_tokens = count_produced_AND_tokens(cromossome)
        number_of_produced_OR_tokens = count_produced_OR_tokens(cromossome)
        max_i = 0
        while not ((number_of_consumed_XOR_tokens == number_of_produced_XOR_tokens) and (number_of_consumed_AND_tokens == number_of_produced_AND_tokens) and (number_of_consumed_OR_tokens == number_of_produced_OR_tokens)) and max_i <= n:
            max_i += 1
            chosen_task = np.random.randint(0, n - 2)
            max_j = 0
            while (cromossome[chosen_task][-1] == 0 or cromossome[chosen_task][-1] == 1) and max_j <= n:
                max_j += 1
                chosen_task = np.random.randint(0, n - 2)
            if max_j <= n:
                cromossome[chosen_task][-1] = 1
                number_of_produced_XOR_tokens = count_produced_XOR_tokens(cromossome)
                number_of_produced_AND_tokens = count_produced_AND_tokens(cromossome)
                number_of_produced_OR_tokens = count_produced_OR_tokens(cromossome)
        if (number_of_consumed_XOR_tokens != number_of_produced_XOR_tokens) or (number_of_consumed_AND_tokens != number_of_produced_AND_tokens) or (number_of_consumed_OR_tokens != number_of_produced_OR_tokens):
            cromossome[:, -1] = copy_of_output_gateways

@njit
def decrease_number_of_consumed_tokens(cromossome, number_of_produced_XOR_tokens, number_of_produced_AND_tokens, number_of_produced_OR_tokens):
    n = len(cromossome)
    copy_of_input_gateways = cromossome[-1].copy()
    number_of_attempts = int(n * 0.5)
    for i in range(number_of_attempts):
        chosen_task = np.random.randint(1, n - 1)
        max_i = 0
        while (cromossome[-1][chosen_task] == 0 or cromossome[-1][chosen_task] == 1) and max_i <= n:
            max_i += 1
            chosen_task = np.random.randint(1, n - 1)
        if max_i <= n:
            cromossome[-1][chosen_task] = 1
        number_of_consumed_XOR_tokens = count_consumed_XOR_tokens(cromossome)
        number_of_consumed_AND_tokens = count_consumed_AND_tokens(cromossome)
        number_of_consumed_OR_tokens = count_consumed_OR_tokens(cromossome)
        max_i = 0
        while not ((number_of_consumed_XOR_tokens == number_of_produced_XOR_tokens) and (number_of_consumed_AND_tokens == number_of_produced_AND_tokens) and (number_of_consumed_OR_tokens == number_of_produced_OR_tokens)) and max_i <= n:
            max_i += 1
            chosen_task = np.random.randint(1, n - 1)
            max_j = 0
            while (cromossome[-1][chosen_task] == 0 or cromossome[-1][chosen_task] == 1) and max_j <= n:
                max_j += 1
                chosen_task = np.random.randint(1, n - 1)
            if max_j <= n:
                cromossome[-1][chosen_task] = 1
                number_of_consumed_XOR_tokens = count_consumed_XOR_tokens(cromossome)
                number_of_consumed_AND_tokens = count_consumed_AND_tokens(cromossome)
                number_of_consumed_OR_tokens = count_consumed_OR_tokens(cromossome)
        if (number_of_consumed_XOR_tokens != number_of_produced_XOR_tokens) or (number_of_consumed_AND_tokens != number_of_produced_AND_tokens) or (number_of_consumed_OR_tokens != number_of_produced_OR_tokens):
            cromossome[-1] = copy_of_input_gateways.copy()

@njit
def is_there_at_least_one_raw_active_task(cromossome, chosen_task):
    row = cromossome[chosen_task]
    for j in range(1, len(row) - 1):
        if row[j] == 1:
            return True
    return False

@njit
def is_there_at_least_one_column_active_task(cromossome, chosen_task):
    for j in range(len(cromossome) - 2):
        if cromossome[j][chosen_task] == 1:
            return True
    return False

@njit
def is_there_at_least_two_raw_active_tasks(cromossome, chosen_task):
    count = 0
    row = cromossome[chosen_task]
    for j in range(1, len(row) - 1):
        if row[j] == 1:
            count += 1
            if count == 2:
                return True
    return False

@njit
def is_there_at_least_two_column_active_tasks(cromossome, chosen_task):
    count = 0
    for j in range(len(cromossome) - 2):
        if cromossome[j][chosen_task] == 1:
            count += 1
            if count == 2:
                return True
    return False

def elitism(population, elitism_percentage, sorted_evaluated_aux_population, sorted_evaluated_population, auxiliary_population, evaluated_aux_population, evaluated_population):
    elitism_count = round(len(population) * elitism_percentage)
    aux_pop_len = len(sorted_evaluated_aux_population)
    total_evaluation_aux_population = evaluated_aux_population[0]
    for i in range(elitism_count):
        aux_index = aux_pop_len - 1 - i
        aux_eval_value, aux_pop_idx = sorted_evaluated_aux_population[aux_index][0], int(
            sorted_evaluated_aux_population[aux_index][5])
        pop_eval_value, pop_idx = sorted_evaluated_population[i][0], int(sorted_evaluated_population[i][5])
        if aux_eval_value < pop_eval_value:
            auxiliary_population[aux_pop_idx] = population[pop_idx]
            total_evaluation_aux_population -= evaluated_aux_population[1][aux_pop_idx][0]
            aux_values = list(evaluated_aux_population[1][aux_pop_idx])
            aux_values[:5] = evaluated_population[1][pop_idx][:5]
            evaluated_aux_population[1][aux_pop_idx] = tuple(aux_values)
            total_evaluation_aux_population += evaluated_aux_population[1][aux_pop_idx][0]
        else:
            break
    evaluated_aux_population[0] = total_evaluation_aux_population

def check_condition(cromossome, source):
    for raw in range(len(cromossome) - 2):
        if not is_there_at_least_one_raw_active_task(cromossome, raw):
            print (1, cromossome, source)
            return False
        if not is_there_at_least_two_raw_active_tasks(cromossome, raw) and cromossome[raw][-1] != 0:
            print (2, cromossome, source)
            return False
        if is_there_at_least_two_raw_active_tasks(cromossome, raw) and cromossome[raw][-1] == 0:
            print (3, cromossome, source)
            return False
    for col in range(1, len(cromossome) - 1):
        if not is_there_at_least_one_column_active_task(cromossome, col):
            print (4, cromossome, source)
            return False
        if (not is_there_at_least_two_column_active_tasks(cromossome, col) and cromossome[-1][col] != 0):
            print (5, cromossome, source)
            return False
        if is_there_at_least_two_column_active_tasks(cromossome, col) and cromossome[-1][col] == 0:
            print (6, cromossome, source)
            return False
    return True