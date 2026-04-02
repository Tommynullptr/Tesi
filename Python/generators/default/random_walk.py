import copy
import random

from Python.generators.terrain.terrain_CA import terrain_CA_from_dungeon, terrain_to_ascii
from Python.generators.objects.place_objects import place_objects_on_terrain
from Python.generators.topology.classify_cells import classify_cells, topo_to_ascii
from Python.measures.measures import Measures
from Python.measures.postprocess import post_process_measures
from Python.meta import Terrain


def generate_random_walk(config, seed = None):
    if seed is None:
        seed = random.randint(0, 2**32 - 1)

    random.seed(seed)

    m = Measures(seed=seed, label="random_measures_" + str(seed), input_params=copy.deepcopy(config))
    m.start_wall()
    
    dungeon = [[Terrain.WALL for _ in range(config["map_width"])] for _ in range(config["map_height"])]

    x, y = config["start"]
    directions = [(1,0), (-1,0), (0,1), (0,-1)]
    dug = 0

    with m.time_phase("dungeon_generation"):
        while dug < config["target_floor"]:
            dungeon[y][x] = Terrain.FLOOR
            dug += 1

            dx, dy = random.choice(directions)
            x = max(1, min(config["map_width"] - 2, x + dx))
            y = max(1, min(config["map_height"] - 2, y + dy))

    with m.time_phase("classify_cells"):
        topo, components, rooms = classify_cells(dungeon, config)
    with m.time_phase("terrain_generation"):
        terrain = terrain_CA_from_dungeon(dungeon, topo, components, config, seed = seed)
    with m.time_phase("objects_generation"):
        objects = place_objects_on_terrain(terrain, topo, config)
    ascii_map = terrain_to_ascii(dungeon, terrain, objects, config)
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

# TODO: versione che non torna sulle stesse celle
