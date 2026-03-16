import random

from Python.generators.terrain.terrain_CA import terrainCAFromDungeon, terrainToAscii
from Python.generators.objects.place_objects import placeObjectsOnTerrain
from Python.generators.topology.classify_cells import classifyCells, topoToAscii
from Python.meta import MAP_WIDTH, MAP_HEIGHT, MIN_ROOM_SIZE, MAX_ROOM_SIZE, MIN_CORRIDOR_SIZE, MAX_CORRIDOR_SIZE, Terrain, START

from collections import deque


def generateLookaheadDungeon(seed = None):
    if seed is None:
        seed = random.randint(0, 2**32 - 1)
    random.seed(seed)

    dungeon = [[Terrain.WALL for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]
    directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    corridor_cells = set()

    # posizione iniziale dell'agente
    agent_x, agent_y = START
    # frontiera da esplorare LIFO, DFS per backtracking
    frontier = deque()
    frontier.append((agent_x, agent_y))
    visited = set()

    def canPlaceRoom(center_x, center_y, width, height, max_overlap_ratio=0.15):
        left = center_x - width // 2
        right = center_x + width // 2
        top = center_y - height // 2
        bottom = center_y + height // 2

        # controllo bounds
        for x in (left, right):
            for y in (top, bottom):
                if not (0 <= x < MAP_WIDTH and 0 <= y < MAP_HEIGHT):
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

    def canPlaceCorridor(center_x, center_y, destination_x, destination_y, length):
        for k in range(1, length):
            new_x = center_x + destination_x * k
            new_y = center_y + destination_y * k

            if not (0 <= new_x < MAP_WIDTH and 0 <= new_y < MAP_HEIGHT):
                return False

            if k < length and dungeon[new_y][new_x] == Terrain.FLOOR:
                return False

        return True

    def placeRoom(center_x, center_y, width, height):
        for i in range(center_x - width // 2, center_x + width // 2 + 1):
            for j in range(center_y - height // 2, center_y + height // 2 + 1):
                dungeon[j][i] = Terrain.FLOOR

    def placeCorridor(center_x, center_y, destination_x, destination_y, length):
        for k in range(length):
            new_x = center_x + destination_x * k
            new_y = center_y + destination_y * k

            if 0 <= new_x < MAP_WIDTH and 0 <= new_y < MAP_HEIGHT:
                dungeon[new_y][new_x] = Terrain.FLOOR
                corridor_cells.add((new_x, new_y))

    # genera tutte le possibili dimensioni di stanza e le mescola ad ogni
    # iterazione per provare a posizionarle in ordine casuale e ridurre bias deterministico verso certe dimensioni
    # IN CHE SENSO BIAS DETERMINISTICO?
    # se le dimensioni sono sempre provate in ordine crescente,
    # è più probabile che vengano posizionate tante stanze piccole e poche grandi,
    # mentre mescolando l'ordine si distribuiscono meglio le dimensioni
    room_sizes = [(width, height) for width in range(MIN_ROOM_SIZE, MAX_ROOM_SIZE) for height in range(MIN_ROOM_SIZE, MAX_ROOM_SIZE)]

    # genere tutte le possibili direzioni
    dirs = directions[:]

    # lunghezze possibili dei corridoi
    lengths = list(range(MIN_CORRIDOR_SIZE, MAX_CORRIDOR_SIZE))

    # algoritmo principale: prova a posizionare stanze e corridoi sulle celle della frontiera,
    # se non riesce più a posizionare nessuno dei due o non ho più celle da esplorare, si ferma
    while frontier:
        agent_x, agent_y = frontier.pop()
        visited.add((agent_x, agent_y))
        flag_r = False

        if not (0 <= agent_x < MAP_WIDTH and 0 <= agent_y < MAP_HEIGHT):
            continue

        random.shuffle(room_sizes)
        random.shuffle(dirs)
        random.shuffle(lengths)

        # prova a posizionare una stanza in quella posizione, se riesce, aggiunge alla frontiera le posizioni attorno alla stanza
        # per esplorare successivamente da lì
        for width, height in room_sizes:
            if canPlaceRoom(agent_x, agent_y, width, height):
                placeRoom(agent_x, agent_y, width, height)
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
                if canPlaceCorridor(agent_x, agent_y, destination_x, destination_y, length):
                    placeCorridor(agent_x, agent_y, destination_x, destination_y, length)

                    end_x = agent_x + destination_x * (length - 1)
                    end_y = agent_y + destination_y * (length - 1)

                    if (end_x, end_y) not in visited:
                        frontier.append((end_x, end_y))

    topo, components = classifyCells(dungeon)
    terrain = terrainCAFromDungeon(dungeon, topo, components, seed = seed)
    objects = placeObjectsOnTerrain(terrain, topo)
    ascii_map = terrainToAscii(dungeon, terrain, objects)
    ascii_topo = topoToAscii(topo)

    return ascii_map, seed, ascii_topo