import copy
import random

from Python.generators.terrain.terrain_CA import terrain_CA_from_dungeon, terrain_to_ascii
from Python.generators.objects.place_objects import place_objects_on_terrain
from Python.generators.topology.classify_cells import classify_cells, topo_to_ascii
from Python.measures.measures import Measures
from Python.measures.postprocess import post_process_measures
from Python.meta import Terrain


# ITERATIONS = numero di iterazioni dell’automa cellulare, raffina la mappa ad ogni iterazione
# secondo la seguente regola: se una cella ha 5 o più muri intorno (8 celle adiacenti), diventa muro, altrimenti pavimento.
def generate_cellular_dungeon(config, seed = None):
    if seed is None:
        seed = random.randint(0, 2 ** 32 - 1)

    random.seed(seed)

    m = Measures(seed=seed, label="cellular_measures_" + str(seed), input_params=copy.deepcopy(config))
    m.start_wall()

    # inizializzazione casuale con una certa probabilità di essere muro o pavimento,
    # al fine di introdurre rumore nella mappa (pavimento casuale),
    # 0 = pavimento, 1 = muro
    dungeon = [[1 if random.random() < config["initial_chance"] else 0
                for _ in range(config["map_width"])]
               for _ in range(config["map_height"])]

    def count_walls(x, y):
        walls = 0

        for j in range(y - 1, y + 2):
            for i in range(x - 1, x + 2):
                if i == x and j == y:
                    continue

                if not (0 <= i < config["map_width"] and 0 <= j < config["map_height"]):
                    walls += 1  # fuori mappa = muro

                elif dungeon[j][i] == 1:
                    walls += 1

        return walls

    # iterazioni dell’automa cellulare
    with m.time_phase("dungeon_generation"):
        for _ in range(config["iterations"]):
            new_map = [[0 for _ in range(config["map_width"])] for _ in range(config["map_height"])]

            for y in range(config["map_height"]):
                for x in range(config["map_width"]):
                    walls = count_walls(x, y)

                    if walls >= config[
                        "num_of_walls"]:  # ciasuna cella evolve in muro se ha abbastanza muri intorno, altrimenti diventa pavimento
                        # TODO: provare a sviluppare regole di evoluzione diverse per le celle
                        new_map[y][x] = 1  # muro

                    else:
                        new_map[y][x] = 0  # pavimento

            dungeon = new_map

        # conversione
        digged_map = [[Terrain.WALL if dungeon[y][x] == 1 else Terrain.FLOOR
                       for x in range(config["map_width"])]
                      for y in range(config["map_height"])]

    with m.time_phase("classify_cells"):
        topo, components, rooms = classify_cells(digged_map, config)
    with m.time_phase("terrain_generation"):
        terrain = terrain_CA_from_dungeon(digged_map, topo, components, config, seed = seed)
    with m.time_phase("objects_generation"):
        objects = place_objects_on_terrain(terrain, topo, config)
    ascii_map = terrain_to_ascii(digged_map, terrain, objects, config)
    ascii_topo = topo_to_ascii(topo, config)

    m.end_wall()

    m.set_meta("dungeon", dungeon)
    m.set_meta("topo", topo)
    m.set_meta("components", components)
    m.set_meta("terrain", terrain)
    m.set_meta("objects", objects)
    m.set_meta("rooms", rooms)

    post_process_measures(m, config)

    return ascii_map, seed, ascii_topo, m
