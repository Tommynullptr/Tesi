import copy
import random

from Python.generators.terrain.terrain_CA import terrain_CA_from_dungeon, terrain_to_ascii
from Python.generators.objects.place_objects import place_objects_on_terrain
from Python.generators.topology.classify_cells import classify_cells, topo_to_ascii
from Python.generators.terrain.terrain_CA import terrain_to_ascii
from Python.measures.measures import Measures
from Python.measures.postprocess import post_process_measures
from Python.meta import Terrain


# Depht-first search maze generation, backtracking iterativo
def generate_maze(config, seed = None):
    if seed is None:
        seed = random.randint(0, 2**32 - 1)

    random.seed(seed)

    m = Measures(seed=seed, label="maze_measures_" + str(seed), input_params=copy.deepcopy(config))
    m.start_wall()

    dungeon = [[Terrain.WALL for _ in range(config["maze_width"])] for _ in range(config["maze_height"])]

    with m.time_phase("dungeon_generation"):
        stack = [(1, 1)]
        visited = set()
        visited.add((1, 1))

        while stack:
            x, y = stack[-1]  # guarda l’ultimo elemento dello stack
            # prendi tutti i vicini validi
            neighbors = []
            for dx, dy in [(2, 0), (-2, 0), (0, 2), (0, -2)]:
                nx, ny = x + dx, y + dy
                if 1 <= nx < config["maze_width"] - 1 and 1 <= ny < config["maze_height"] - 1:
                    if (nx, ny) not in visited:
                        neighbors.append((nx, ny))

            if neighbors:
                nx, ny = random.choice(neighbors)  # scegli un vicino casuale
                # scava il muro intermedio
                dungeon[y + (ny - y) // 2][x + (nx - x) // 2] = Terrain.FLOOR
                dungeon[ny][nx] = Terrain.FLOOR
                visited.add((nx, ny))
                stack.append((nx, ny))  # aggiungi al percorso
            else:
                stack.pop()  # backtracking quando non ci sono vicini

    with m.time_phase("classify_cells"):
        topo, components, rooms = classify_cells(dungeon, config, maze = True)
    with m.time_phase("terrain_generation"):
        terrain = terrain_CA_from_dungeon(dungeon, topo, components, config, seed=seed, maze = True)
    with m.time_phase("objects_generation"):
        objects = place_objects_on_terrain(terrain, topo, config, maze = True)
    ascii_map = terrain_to_ascii(dungeon, terrain, objects, config, maze = True)
    ascii_topo = topo_to_ascii(topo, config, maze = True)

    m.end_wall()

    m.set_meta("dungeon", dungeon)
    m.set_meta("topo", topo)
    m.set_meta("components", components)
    m.set_meta("terrain", terrain)
    m.set_meta("objects", objects)
    m.set_meta("rooms", rooms)

    post_process_measures(m, config, maze = True)

    return ascii_map, seed, ascii_topo, m