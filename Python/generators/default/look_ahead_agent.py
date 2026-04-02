import copy
import random

from Python.generators.terrain.terrain_CA import terrain_CA_from_dungeon, terrain_to_ascii
from Python.generators.objects.place_objects import place_objects_on_terrain
from Python.generators.topology.classify_cells import classify_cells, topo_to_ascii
from Python.measures.measures import Measures
from Python.measures.postprocess import post_process_measures
from Python.meta import Terrain

from collections import deque


def generate_lookahead_dungeon(config, seed = None):
    if seed is None:
        seed = random.randint(0, 2**32 - 1)

    random.seed(seed)

    m = Measures(seed=seed, label="lookahead_measures_" + str(seed), input_params=copy.deepcopy(config))
    m.start_wall()

    dungeon = [[Terrain.WALL for _ in range(config["map_width"])] for _ in range(config["map_height"])]
    directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    corridor_cells = set()

    # posizione iniziale dell'agente
    agent_x, agent_y = config["start"]
    # frontiera da esplorare LIFO, DFS per backtracking
    frontier = deque()
    frontier.append((agent_x, agent_y))
    visited = set()

    def can_place_room(center_x, center_y, width, height, max_overlap_ratio=0.15):
        left = center_x - width // 2
        right = center_x + width // 2
        top = center_y - height // 2
        bottom = center_y + height // 2

        # controllo bounds
        for x in (left, right):
            for y in (top, bottom):
                if not (0 <= x < config["map_width"] and 0 <= y < config["map_height"]):
                    return False

        overlap_coords = []
        total_cells = (right - left + 1) * (bottom - top + 1)

        # raccogli tutte le floor nella box
        for x in range(left, right + 1):
            for y in range(top, bottom + 1):
                if dungeon[y][x] == Terrain.FLOOR:
                    overlap_coords.append((x, y))

        # se non ci sono overlap, ok
        if not overlap_coords:
            return True

        # percentuale di overlap
        overlap_count = len(overlap_coords)
        overlap_ratio = overlap_count / float(total_cells)

        if overlap_ratio > max_overlap_ratio:
            return False

        # tutte le overlap devono essere corridoio (non stanze già piazzate)
        for (x, y) in overlap_coords:
            if (x, y) not in corridor_cells:
                return False

        return True

    def can_place_corridor(center_x, center_y, destination_x, destination_y, length):
        for k in range(1, length):
            new_x = center_x + destination_x * k
            new_y = center_y + destination_y * k

            if not (0 <= new_x < config["map_width"] and 0 <= new_y < config["map_height"]):
                return False

            if k < length and dungeon[new_y][new_x] == Terrain.FLOOR:
                return False

        return True

    def place_room(center_x, center_y, width, height):
        for i in range(center_x - width // 2, center_x + width // 2 + 1):
            for j in range(center_y - height // 2, center_y + height // 2 + 1):
                dungeon[j][i] = Terrain.FLOOR

    def place_corridor(center_x, center_y, destination_x, destination_y, length):
        for k in range(length):
            new_x = center_x + destination_x * k
            new_y = center_y + destination_y * k

            if 0 <= new_x < config["map_width"] and 0 <= new_y < config["map_height"]:
                dungeon[new_y][new_x] = Terrain.FLOOR
                corridor_cells.add((new_x, new_y))

    # genera tutte le possibili dimensioni di stanza e le mescola ad ogni
    # iterazione per provare a posizionarle in ordine casuale e ridurre bias deterministico verso certe dimensioni
    # IN CHE SENSO BIAS DETERMINISTICO?
    # se le dimensioni sono sempre provate in ordine crescente,
    # è più probabile che vengano posizionate tante stanze piccole e poche grandi,
    # mentre mescolando l'ordine si distribuiscono meglio le dimensioni
    room_sizes = [(width, height) for width in range(config["min_room_size"], config["max_room_size"]) for height in range(config["min_room_size"], config["max_room_size"])]

    # genere tutte le possibili direzioni
    dirs = directions[:]

    # lunghezze possibili dei corridoi
    lengths = list(range(config["min_corridor_size"], config["max_corridor_size"]))

    # algoritmo principale: prova a posizionare stanze e corridoi sulle celle della frontiera,
    # se non riesce più a posizionare nessuno dei due o non ho più celle da esplorare, si ferma
    with m.time_phase("dungeon_generation"):
       while frontier:
           agent_x, agent_y = frontier.pop()
           visited.add((agent_x, agent_y))
           flag_r = False

           if not (0 <= agent_x < config["map_width"] and 0 <= agent_y < config["map_height"]):
               continue

           random.shuffle(room_sizes)
           random.shuffle(dirs)
           random.shuffle(lengths)

           # prova a posizionare una stanza in quella posizione, se riesce, aggiunge alla frontiera le posizioni attorno alla stanza
           # per esplorare successivamente da lì
           for width, height in room_sizes:
               if can_place_room(agent_x, agent_y, width, height):
                   place_room(agent_x, agent_y, width, height)
                   flag_r = True

                   left = agent_x - width // 2
                   right = agent_x + width // 2
                   top = agent_y - height // 2
                   bottom = agent_y + height // 2

                   candidates = [(left, agent_y), (right, agent_y), (agent_x, top), (agent_x, bottom)]
                   # mescola casualmente
                   random.shuffle(candidates)

                   # push sulla frontier
                   for new_x, new_y in candidates:
                       if (new_x, new_y) not in visited:
                           frontier.append((new_x, new_y))

                   break

           if flag_r:
               continue

           # prova a posizionare un corridoio in una delle direzioni,
           # se riesce, aggiunge alla frontiera la posizione finale del corridoio per esplorare successivamente da lì
           for destination_x, destination_y in dirs:
               for length in lengths:
                   if can_place_corridor(agent_x, agent_y, destination_x, destination_y, length):
                       place_corridor(agent_x, agent_y, destination_x, destination_y, length)

                       end_x = agent_x + destination_x * (length - 1)
                       end_y = agent_y + destination_y * (length - 1)

                       if (end_x, end_y) not in visited:
                           frontier.append((end_x, end_y))

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