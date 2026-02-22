# Parametri globali

MAPS_AMOUNT = 5 # numero di mappe da generare per ogni algoritmo

# Dimensioni di default della mappa
MAP_WIDTH = 160
MAP_HEIGHT = 100

# Dimensioni delle stanze e corridoi
MIN_ROOM_SIZE = 5
MAX_ROOM_SIZE = 25
MIN_CORRIDOR_SIZE = 5
MAX_CORRIDOR_SIZE = 15

# Parametri per algoritmi specifici
TARGET_FLOOR = (MAP_WIDTH * MAP_HEIGHT) // 1  # random_walk
MIN_NODE_SIZE = 20  # BSP
MAX_NODE_SIZE = 40  # BSP
INITIAL_CHANCE = 0.45  # cellular automata
ITERATIONS = 5        # cellular automata

# Per maze_generation.py
MAZE_WIDTH = 161   # deve essere dispari
MAZE_HEIGHT = 101  # deve essere dispari