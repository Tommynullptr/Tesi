import random

from Python.generators.objects.place_objects import placeObjectsOnTerrain
from Python.generators.topology.classify_cells import classifyCells, topoToAscii
from Python.generators.terrain.terrain_CA import terrainCAFromDungeon, terrainToAscii
from Python.meta import MAP_WIDTH, MAP_HEIGHT, MIN_ROOM_SIZE, MAX_ROOM_SIZE, Terrain, START, PROB_ROOM, PROB_CORRIDOR, TARGET_FLOOR


def generateBlindDungeon(seed = None):
    if seed is None:
        seed = random.randint(0, 2**32 - 1) # genera un seed casuale se non è stato fornito

    random.seed(seed)
    dungeon = [[Terrain.WALL for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]

    # Probabilità iniziali
    prob_corridor = PROB_CORRIDOR   # Prob. di cambiare direzione (corridoio)
    prob_room = PROB_ROOM   # Prob. di creare una stanza

    # Direzioni possibili
    directions = [(1,0), (-1,0), (0,1), (0,-1)]

    # Posizione iniziale dell'agente
    agent_x, agent_y = START
    destination_x, destination_y = random.choice(directions)

    # funzione per scavare
    def dig(agent_x, agent_y):
        if 0 <= agent_x < MAP_WIDTH and 0 <= agent_y < MAP_HEIGHT: # controllo che l'agente sia dentro la mappa
            dungeon[agent_y][agent_x] = Terrain.FLOOR

    # funzione per creare una stanza
    def createRoom(center_x, center_y):
        room_width = random.randint(MIN_ROOM_SIZE, MAX_ROOM_SIZE)
        room_height = random.randint(MIN_ROOM_SIZE, MAX_ROOM_SIZE)

        for i in range(center_x - room_width//2, center_x + room_width//2 + 1): # scorro sulla larghezza della stanza
            for j in range(center_y - room_height//2, center_y + room_height//2 + 1): # scorro sull'altezza della stanza
                if 0 <= i < MAP_WIDTH and 0 <= j < MAP_HEIGHT:
                    dungeon[j][i] = Terrain.FLOOR

    # condizione di stop: numero minimo di celle scavate
    target_floor = TARGET_FLOOR
    dug = 0

    while dug < target_floor:
        dig(agent_x, agent_y)
        dug += 1

        # utilizzo le probabilità per decidere se cambiare direzione o creare una stanza
        # step 5: roll number_c
        number_c = random.randint(0, 100)

        if number_c < prob_corridor:
            destination_x, destination_y = random.choice(directions)
            prob_corridor = 0

        else:
            prob_corridor += 5 # aumento la probabilità di cambiare direzione se non è successo

        # step 11: roll number_r
        number_r = random.randint(0, 100)

        if number_r < prob_room:
            createRoom(agent_x, agent_y)
            prob_room = 0

        else:
            prob_room += 1

        # muovo l'agente
        agent_x += destination_x
        agent_y += destination_y

        # evita di uscire dalla mappa
        if agent_x <= 1 or agent_x >= MAP_WIDTH - 2:
            destination_x = -destination_x

        if agent_y <= 1 or agent_y >= MAP_HEIGHT - 2:
            destination_y = -destination_y

    topo, components = classifyCells(dungeon)
    terrain = terrainCAFromDungeon(dungeon, topo, components, seed = seed)
    objects = placeObjectsOnTerrain(terrain, topo)
    ascii_map = terrainToAscii(dungeon, terrain, objects)
    ascii_topo = topoToAscii(topo)

    return ascii_map, seed, ascii_topo
