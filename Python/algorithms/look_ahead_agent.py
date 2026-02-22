import random
from Python.meta import MAP_WIDTH, MAP_HEIGHT, MIN_ROOM_SIZE, MAX_ROOM_SIZE, MIN_CORRIDOR_SIZE, MAX_CORRIDOR_SIZE


def generate_lookahead_dungeon():

    dungeon = [["#" for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]

    directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]

    # posizione iniziale dell'agente
    agent_x = random.randint(5, MAP_WIDTH - 6)
    agent_y = random.randint(5, MAP_HEIGHT - 6)

    def can_place_room(center_x, center_y, width, height):
        for i in range(center_x - width // 2, center_x + width // 2 + 1):
            for j in range(center_y - height // 2, center_y + height // 2 + 1):

                if not (0 <= i < MAP_WIDTH and 0 <= j < MAP_HEIGHT):
                    return False

                if dungeon[j][i] == "r":
                    return False

        return True

    def can_place_corridor(center_x, center_y, destination_x, destination_y, length):
        for k in range(1, length):
            new_x = center_x + destination_x * k
            new_y = center_y + destination_y * k

            if not (0 <= new_x < MAP_WIDTH and 0 <= new_y < MAP_HEIGHT):
                return False

            if k < length - 1 and dungeon[new_y][new_x] == "c":
                return False

        return True

    def place_room(center_x, center_y, width, height):
        for i in range(center_x - width // 2, center_x + width // 2 + 1):
            for j in range(center_y - height // 2, center_y + height // 2 + 1):
                dungeon[j][i] = "r"

    def place_corridor(center_x, center_y, destination_x, destination_y, length):
        for k in range(length):
            new_x = center_x + destination_x * k
            new_y = center_y + destination_y * k

            if 0 <= new_x < MAP_WIDTH and 0 <= new_y < MAP_HEIGHT:
                dungeon[new_y][new_x] = "c"

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
            if can_place_room(agent_x, agent_y, width, height):
                place_room(agent_x, agent_y, width, height)
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
                if can_place_corridor(agent_x, agent_y, destination_x, destination_y, length):
                    place_corridor(agent_x, agent_y, destination_x, destination_y, length)
                    flag_c = 1

                    # estremità del corridoio (ultimo tile scavato)
                    agent_x += destination_x * (length - 1)
                    agent_y += destination_y * (length - 1)

                    break

        if not (0 <= agent_x < MAP_WIDTH and 0 <= agent_y < MAP_HEIGHT):
            break

        if flag_c == 0 and flag_r == 0:
            break

    # converte i simboli "r" e "c" in "." per avere una mappa finale in ASCII
    for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):
            if dungeon[y][x] == "r" or dungeon[y][x] == "c":
                dungeon[y][x] = "."

    return dungeon