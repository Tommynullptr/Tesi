import random

from Python.meta import MAP_WIDTH, MAP_HEIGHT, INITIAL_CHANCE, ITERATIONS

# ITERATIONS = numero di iterazioni dell’automa cellulare, raffina la mappa ad ogni iterazione
# secondo la seguente regola: se una cella ha 5 o più muri intorno (8 celle adiacenti), diventa muro, altrimenti pavimento.

def generate_cellular_dungeon(map_w=MAP_WIDTH, map_h=MAP_HEIGHT):
    # TODO: introdurre rumore (muri casuali) per far evolvere la mappa in modo più vario
    # inizializzazione casuale
    # 0 = pavimento, 1 = muro
    dungeon = [[1 if random.random() < INITIAL_CHANCE else 0
                for _ in range(map_w)]
               for _ in range(map_h)]

    def count_walls(x, y):
        walls = 0

        for j in range(y - 1, y + 2):
            for i in range(x - 1, x + 2):

                if i == x and j == y:
                    continue
                if not (0 <= i < map_w and 0 <= j < map_h):
                    walls += 1  # fuori mappa = muro
                elif dungeon[j][i] == 1:
                    walls += 1

        return walls

    # iterazioni dell’automa cellulare
    for _ in range(ITERATIONS):
        new_map = [[0 for _ in range(map_w)] for _ in range(map_h)]

        for y in range(map_h):
            for x in range(map_w):
                walls = count_walls(x, y)

                if walls >= 5: # ciasuna cella evolve in muro se ha 5 o più muri intorno, altrimenti diventa pavimento
                    # TODO: provare a sviluppare regole di evoluzione diverse per le celle
                    new_map[y][x] = 1  # muro
                else:
                    new_map[y][x] = 0  # pavimento

        dungeon = new_map

    # conversione (in ASCII)
    ascii_map = [["#" if dungeon[y][x] == 1 else "."
                  for x in range(map_w)]
                 for y in range(map_h)]

    return ascii_map
