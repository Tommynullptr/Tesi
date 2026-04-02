import random
import copy

from Python.generators.objects.place_objects import place_objects_on_terrain
from Python.generators.topology.classify_cells import classify_cells, topo_to_ascii
from Python.generators.terrain.terrain_CA import terrain_CA_from_dungeon, terrain_to_ascii
from Python.measures.measures import Measures
from Python.measures.postprocess import post_process_measures
from Python.meta import Terrain


def generate_blind_dungeon(config, seed = None):
    if seed is None:
        seed = random.randint(0, 2**32 - 1) # genera un seed casuale se non è stato fornito

    random.seed(seed)

    m = Measures(seed=seed, label="blind_measures_" + str(seed), input_params=copy.deepcopy(config))
    m.start_wall()

    dungeon = [[Terrain.WALL for _ in range(config["map_width"])] for _ in range(config["map_height"])]

    # Probabilità iniziali
    prob_corridor = config["prob_corridor"]   # Prob. di cambiare direzione (corridoio)
    prob_room = config["prob_room"]   # Prob. di creare una stanza

    # Direzioni possibili
    directions = [(1,0), (-1,0), (0,1), (0,-1)]

    # Posizione iniziale dell'agente
    agent_x, agent_y = config["start"]
    destination_x, destination_y = random.choice(directions)

    # funzione per scavare
    def dig(agent_x, agent_y):
        if 0 <= agent_x < config["map_width"] and 0 <= agent_y < config["map_height"]: # controllo che l'agente sia dentro la mappa
            dungeon[agent_y][agent_x] = Terrain.FLOOR

    # funzione per creare una stanza
    def createRoom(center_x, center_y):
        room_width = random.randint(config["min_room_size"], config["max_room_size"])
        room_height = random.randint(config["min_room_size"], config["max_room_size"])

        for i in range(center_x - room_width//2, center_x + room_width//2 + 1): # scorro sulla larghezza della stanza
            for j in range(center_y - room_height//2, center_y + room_height//2 + 1): # scorro sull'altezza della stanza
                if 0 <= i < config["map_width"] and 0 <= j < config["map_height"]:
                    dungeon[j][i] = Terrain.FLOOR

    # condizione di stop: numero minimo di celle scavate
    target_floor = config["target_floor"]
    dug = 0

    with m.time_phase("dungeon_generation"):
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
                prob_corridor += 5  # aumento la probabilità di cambiare direzione se non è successo

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
            if agent_x <= 1 or agent_x >= config["map_width"] - 2:
                destination_x = -destination_x

            if agent_y <= 1 or agent_y >= config["map_height"] - 2:
                destination_y = -destination_y

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
