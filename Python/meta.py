from enum import IntEnum

# Parametri globali
MAPS_AMOUNT = 10 # numero di mappe da generare per ogni algoritmo
MAP_WIDTH = 160
MAP_HEIGHT = 100
START = (MAP_WIDTH // 2, MAP_HEIGHT // 2) # posizione iniziale
TARGET_FLOOR = (MAP_WIDTH * MAP_HEIGHT) // 2  # terreno da scavare

# Dimensioni delle stanze e corridoi
MIN_ROOM_SIZE = 5
MAX_ROOM_SIZE = 25
MIN_CORRIDOR_SIZE = 5
MAX_CORRIDOR_SIZE = 15

# Parametri per algoritmi specifici:
# BSP
MIN_NODE_SIZE = 20
MAX_NODE_SIZE = 40

# cellular automata
INITIAL_CHANCE = 0.5
ITERATIONS = 5
NUM_OF_WALLS = 5

# blind agent
PROB_CORRIDOR = 5
PROB_ROOM = 5

# maze
MAZE_WIDTH = 161   # deve essere dispari
MAZE_HEIGHT = 101  # deve essere dispari

# Costanti terreno e topologia
class Terrain(IntEnum):
    WALL = 0
    FLOOR = 1
    GROUND = 2
    GRASS = 3
    WATER = 4

class Topo(IntEnum):
    FLOOR = 0 # terreno generico
    ROOM = 1
    CORRIDOR = 2
    JUNCTION = 3 # per i corridoi
    DEADEND = 4

# Parametri per terreni
MIN_ROOM_SIZE_FOR_LAKE = 15