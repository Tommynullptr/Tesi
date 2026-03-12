import random

from Python.generators.terrain.terrain_CA import terrainCAFromDungeon, terrainToAscii
from Python.generators.objects.place_objects import placeObjectsOnTerrain
from Python.generators.topology.classify_cells import classifyCells, topoToAscii
from Python.meta import MAP_WIDTH, MAP_HEIGHT, MIN_ROOM_SIZE, MAX_ROOM_SIZE, MIN_CORRIDOR_SIZE, MAX_CORRIDOR_SIZE, Terrain, START, Topo


def generateLookaheadDungeon(seed=None):
    if seed is None:
        seed = random.randint(0, 2**32 - 1)

    random.seed(seed)

    dungeon = [[Terrain.WALL for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]
    directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    # il look ahead agent tiene traccia della topologia della mappa
    # per prendere decisioni su dove posizionare le stanze e i corridoi successivi
    topo = [[Topo.FLOOR] * MAP_WIDTH for _ in range(MAP_HEIGHT)]

    # posizione iniziale dell'agente
    agent_x, agent_y = START

    def canPlaceRoom(center_x, center_y, width, height):
        for i in range(center_x - width // 2, center_x + width // 2 + 1):
            for j in range(center_y - height // 2, center_y + height // 2 + 1):
                if not (0 <= i < MAP_WIDTH and 0 <= j < MAP_HEIGHT):
                    return False

                if topo[j][i] == Topo.ROOM:# or topo[j][i] == Topo.CORRIDOR:
                    return False

        return True

    def canPlaceCorridor(center_x, center_y, destination_x, destination_y, length):
        for k in range(1, length):
            new_x = center_x + destination_x * k
            new_y = center_y + destination_y * k

            if not (0 <= new_x < MAP_WIDTH and 0 <= new_y < MAP_HEIGHT):
                return False

            if k < length and topo[new_y][new_x] == Topo.ROOM:
                return False

        return True

    def placeRoom(center_x, center_y, width, height):
        for i in range(center_x - width // 2, center_x + width // 2 + 1):
            for j in range(center_y - height // 2, center_y + height // 2 + 1):
                dungeon[j][i] = Terrain.FLOOR
                topo[j][i] = Topo.ROOM

    def placeCorridor(center_x, center_y, destination_x, destination_y, length):
        for k in range(length):
            new_x = center_x + destination_x * k
            new_y = center_y + destination_y * k

            if 0 <= new_x < MAP_WIDTH and 0 <= new_y < MAP_HEIGHT:
                dungeon[new_y][new_x] = Terrain.FLOOR
                topo[new_y][new_x] = Topo.CORRIDOR

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

    # algoritmo principale: prova a posizionare stanze e corridoi, se non riesce più a posizionare nessuno dei due, si ferma
    while True:
        flag_r = 0
        flag_c = 0

        random.shuffle(room_sizes)
        random.shuffle(dirs)
        random.shuffle(lengths)

        # prova a posizionare una stanza in quella posizione, se riesce, aggiunge al stack le posizioni attorno alla stanza per esplorare da lì
        for width, height in room_sizes:
            if canPlaceRoom(agent_x, agent_y, width, height):
                placeRoom(agent_x, agent_y, width, height)
                flag_r = 1

                # sposta l'agente di una direzione casuale più l'altezza o la larghezza della stanza
                destination_x, destination_y = random.choice(directions)
                if destination_x != 0:
                    agent_x += destination_x * (width // 2 + 1)
                else:
                    agent_y += destination_y * (height // 2 + 1)

                break

        if not (0 <= agent_x < MAP_WIDTH and 0 <= agent_y < MAP_HEIGHT):
            break

        # prova a posizionare un corridoio in una delle direzioni,
        # se riesce, sposta l'agente alla fine del corridoio e continua da lì
        for destination_x, destination_y in dirs:
            for length in lengths:
                if canPlaceCorridor(agent_x, agent_y, destination_x, destination_y, length):
                    placeCorridor(agent_x, agent_y, destination_x, destination_y, length)
                    flag_c = 1

                    # estremità del corridoio (ultimo tile scavato)
                    agent_x += destination_x * (length - 1)
                    agent_y += destination_y * (length - 1)

                    break

        if not (0 <= agent_x < MAP_WIDTH and 0 <= agent_y < MAP_HEIGHT):
            break

        if flag_c == 0 and flag_r == 0:
            break

    new_topo, components = classifyCells(dungeon, topo)
    terrain = terrainCAFromDungeon(dungeon, new_topo, components, seed = seed)
    objects = placeObjectsOnTerrain(terrain, new_topo)
    ascii_map = terrainToAscii(dungeon, terrain, objects)
    ascii_topo = topoToAscii(new_topo)

    return ascii_map, seed, ascii_topo