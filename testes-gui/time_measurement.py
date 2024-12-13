"""
Este arquivo tem como objetivo formalizar as tentativas de melhorar o alg de XP

Autor: Guilherme Fernandes da Costa

Material de apoio usado:
    >  ChatGPT, StackOverFlow, Vozes da Minha cabeça
"""

# 1 - tentando identificar a passagem de tempo em cada uma das funçoes do projeto
# exemplo do quicksort - penso em utilizar o jupiter, ja que ele possui um sistema de benchmark

#Imports necessarios
import numpy as np
import pandas as pd
import timeit

#Preparando os registros para o quicksort
def gerar_registros(filename, num_registros=100):
    # Gera uma coluna de IDs de 1 a num_registros
    ids = np.arange(1, num_registros + 1)

    # Gera uma coluna de sequências de 8 bits
    bits_sequencias = [''.join(np.random.choice(['0', '1'], 8)) for _ in range(num_registros)]

    # Cria um DataFrame com os dados
    df = pd.DataFrame({'ID': ids, 'Bits': bits_sequencias})

    # Salva o DataFrame em um arquivo .txt no formato CSV
    df.to_csv(filename, index=False, header=False)

#Manipular o arquivo 'registros.txt'
def ler_registros(filename):
    with open(filename, 'r') as file:
        # Lê o arquivo e separa os dados em uma lista de tuplas
        registros = [line.strip().split(',') for line in file]
    return [(int(reg[0]), reg[1]) for reg in registros]  # Converte ID para int

def salvar_registros(filename, registros):
    with open(filename, 'w') as file:
        for id_num, bits in registros:
            file.write(f"{id_num},{bits}\n")

# def ordenar_registros():
#     return np.sort(registros,kind='quicksort')

#quicksort
def quicksort_por_valor(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2][1]  # Pivô é o valor da sequência de bits
    left = [x for x in arr if x[1] < pivot]
    middle = [x for x in arr if x[1] == pivot]
    right = [x for x in arr if x[1] > pivot]
    return quicksort_por_valor(left) + middle + quicksort_por_valor(right)

def medir_tempo_ordenacao_por_valor(filename):
    # Lê os registros
    registros = ler_registros(filename)

    # Define uma função local para ordenar os registros
    def ordenar_por_valor():
        return quicksort_por_valor(registros)

    # tempo_crossover = timeit.timeit(crossover(pop, ...), number=1)
    # tempo_crossover --> plotar em grafico // mudumos de ideia criar tabela (arquivo .xlsx --> fundamental para fazer analises)
    # Mede o tempo de execução
    tempo_gasto = timeit.timeit(ordenar_por_valor, number=1)
    print(f"Tempo gasto para ordenar por valor: {tempo_gasto:.6f} segundos")

    # Ordena os registros e salva em um novo arquivo
    registros_ordenados = ordenar_por_valor()
    salvar_registros('registros_ordenados_por_valor.txt', registros_ordenados)
    return registros_ordenados

#Main()

# Gerar o arquivo com 100 registros
gerar_registros('registros.txt')
#Ler o arquivo
# registros= ler_registros('registros.txt')
medir_tempo_ordenacao_por_valor('registros.txt')

# print("Lista ordenada:", arr_sorted)
