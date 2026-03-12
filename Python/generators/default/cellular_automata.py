import random

from Python.generators.terrain.terrain_CA import terrainCAFromDungeon, terrainToAscii
from Python.generators.objects.place_objects import placeObjectsOnTerrain
from Python.generators.topology.classify_cells import classifyCells, topoToAscii
from Python.meta import MAP_WIDTH, MAP_HEIGHT, INITIAL_CHANCE, ITERATIONS, Terrain, NUM_OF_WALLS


# ITERATIONS = numero di iterazioni dell’automa cellulare, raffina la mappa ad ogni iterazione
# secondo la seguente regola: se una cella ha 5 o più muri intorno (8 celle adiacenti), diventa muro, altrimenti pavimento.
def generateCellularDungeon(map_w=MAP_WIDTH, map_h=MAP_HEIGHT, seed = None):
    if seed is None:
        seed = random.randint(0, 2 ** 32 - 1)

    random.seed(seed)

    # inizializzazione casuale con una certa probabilità di essere muro o pavimento,
    # al fine di introdurre rumore nella mappa (pavimento casuale),
    # 0 = pavimento, 1 = muro
    dungeon = [[1 if random.random() < INITIAL_CHANCE else 0
                for _ in range(map_w)]
               for _ in range(map_h)]

    def countWalls(x, y):
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
                walls = countWalls(x, y)

                if walls >= NUM_OF_WALLS: # ciasuna cella evolve in muro se ha abbastanza muri intorno, altrimenti diventa pavimento
                    # TODO: provare a sviluppare regole di evoluzione diverse per le celle
                    new_map[y][x] = 1  # muro

                else:
                    new_map[y][x] = 0  # pavimento

        dungeon = new_map

    # conversione
    digged_map = [[Terrain.WALL if dungeon[y][x] == 1 else Terrain.FLOOR
                  for x in range(map_w)]
                 for y in range(map_h)]

    topo, components = classifyCells(digged_map)
    terrain = terrainCAFromDungeon(digged_map, topo, components, seed = seed)
    objects = placeObjectsOnTerrain(terrain, topo)
    ascii_map = terrainToAscii(digged_map, terrain, objects)
    ascii_topo = topoToAscii(topo)

    return ascii_map, seed, ascii_topo
