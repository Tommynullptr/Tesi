import random
from Python.meta import MAP_WIDTH, MAP_HEIGHT, MIN_ROOM_SIZE, MAX_ROOM_SIZE

def generate_agent_dungeon():

    dungeon = [["#" for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]

    # Probabilità iniziali
    prob_c = 5   # Prob. di cambiare direzione (corridoio)
    prob_r = 5   # Prob. di creare una stanza

    # Direzioni possibili
    directions = [(1,0), (-1,0), (0,1), (0,-1)]

    # Posizione iniziale dell'agente
    agent_x = MAP_WIDTH // 2
    agent_y = MAP_HEIGHT // 2
    destination_x, destination_y = random.choice(directions)

    # funzione per scavare
    def dig(agent_x, agent_y):
        if 0 <= agent_x < MAP_WIDTH and 0 <= agent_y < MAP_HEIGHT: # controllo che agent_x e agent_y siano validi
            dungeon[agent_y][agent_x] = "."

    # funzione per creare una stanza
    def create_room(center_x, center_y):
        w = random.randint(MIN_ROOM_SIZE, MAX_ROOM_SIZE)
        h = random.randint(MIN_ROOM_SIZE, MAX_ROOM_SIZE)

        for i in range(center_x - w//2, center_x + w//2 + 1): # scorro sulla larghezza della stanza
            for j in range(center_y - h//2, center_y + h//2 + 1): # scorro sull'altezza della stanza
                if 0 <= i < MAP_WIDTH and 0 <= j < MAP_HEIGHT:
                    dungeon[j][i] = "."

    # condizione di stop: numero minimo di celle scavate
    target_floor = (MAP_WIDTH * MAP_HEIGHT) // 3
    dug = 0

    while dug < target_floor:
        
        dig(agent_x, agent_y)
        dug += 1

        # utilizzo le probabilità per decidere se cambiare direzione o creare una stanza
        # step 5: roll number_c
        number_c = random.randint(0, 100)
        if number_c < prob_c:
            destination_x, destination_y = random.choice(directions)
            prob_c = 0
        else:
            prob_c += 5

        # step 11: roll number_r
        number_r = random.randint(0, 100)
        if number_r < prob_r:
            create_room(agent_x, agent_y)
            prob_r = 0
        else:
            prob_r += 5

        # muovo l'agente
        agent_x += destination_x
        agent_y += destination_y

        # evita di uscire dalla mappa
        if agent_x <= 1 or agent_x >= MAP_WIDTH - 2:
            destination_x = -destination_x
        if agent_y <= 1 or agent_y >= MAP_HEIGHT - 2:
            destination_y = -destination_y

    return dungeon
