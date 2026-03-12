from collections import deque

from Python.meta import MAP_WIDTH, MAP_HEIGHT, MIN_ROOM_SIZE, Topo, Terrain


# Classificazione topologica (TOPO) usata per decisioni mirate sul popolamento del terreno:
# etichettare ogni cella come stanza/corridoio/incrocio/dead-end permette regole locali
# semplici ed efficienti (O(N)) per spawn di oggetti evitando di
# piazzarli in luoghi non consoni come corridoi o terreno diverso; inoltre fornisce
# contesto di area (component id) utile per posizionare elementi su stanze grandi.
def classifyCells(dungeon, topo=None):
    if topo is None:
        topo = [[Topo.FLOOR] * MAP_WIDTH for _ in range(MAP_HEIGHT)]

    deg = [[0] * MAP_WIDTH for _ in range(MAP_HEIGHT)]  # degree of floor cell in 4-neighborhood
    # il grado di una cella è il numero di celle adiacenti che sono pavimento;
    # usato per classificare dead-end (1), corridoio (2), junction (3+)
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    # computa il grado di ogni cella di pavimento contando quante celle adiacenti
    # sono anch'esse pavimento; questo grado è usato per classificare le celle
    for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):

            if dungeon[y][x] == Terrain.FLOOR:
                count_floor = 0

                for direction_x, direction_y in directions:
                    new_x, new_y = x + direction_x, y + direction_y

                    if 0 <= new_x < MAP_WIDTH and 0 <= new_y < MAP_HEIGHT and dungeon[new_y][new_x] == Terrain.FLOOR:
                        count_floor += 1

                deg[y][x] = count_floor  # conto quanto floor ho attorno (degree di una cella)

    # segna deadend, corridor, junction attraverso deg
    for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):

            if dungeon[y][x] == Terrain.FLOOR:
                degree = deg[y][x]

                if degree == 1:
                    topo[y][x] = Topo.DEADEND

                elif degree == 2:
                    topo[y][x] = Topo.CORRIDOR

                else:
                    topo[y][x] = Topo.JUNCTION

            else:
                topo[y][x] = None  # wall

    # identifica componenti connesse di pavimento usando BFS e assegna un id a ciascuna componente
    component_id = [[-1] * MAP_WIDTH for _ in range(MAP_HEIGHT)]
    counter_id = 0
    components = {}

    for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):

            if dungeon[y][x] == Terrain.FLOOR and component_id[y][x] == -1:
                queue = deque([(x, y)]) # BFS
                component_id[y][x] = counter_id
                cells = [(x, y)]

                while queue:
                    cell_x, cell_y = queue.popleft()

                    for direction_x, direction_y in directions:
                        new_x, new_y = cell_x + direction_x, cell_y + direction_y

                        if (0 <= new_x < MAP_WIDTH and 0 <= new_y < MAP_HEIGHT and
                                dungeon[new_y][new_x] == Terrain.FLOOR and component_id[new_y][new_x] == -1 and 
                                topo[new_y][new_x] != Topo.CORRIDOR and topo[new_y][new_x] != Topo.DEADEND):
                            component_id[new_y][new_x] = counter_id
                            queue.append((new_x, new_y))
                            cells.append((new_x, new_y))

                components[counter_id] = cells
                counter_id += 1

    # Riconoscimento stanze tramite bounding box e fill ratio
    for _, cells in components.items():
        component_size = len(cells)
        
        if component_size < MIN_ROOM_SIZE:
            continue  # troppo piccola per essere stanza

        # bounding box della componente
        # la costruisco raccogliendo tutte le coordinate x e y delle celle
        component_x_coords = [x for (x, y) in cells]
        component_y_coords = [y for (x, y) in cells]

        bounding_box_width = max(component_x_coords) - min(component_x_coords) + 1
        bounding_box_height = max(component_y_coords) - min(component_y_coords) + 1

        # rapporto di riempimento
        # misura quando la bounding box è riempita dalle celle effettive della componente
        fill_ratio = component_size / (bounding_box_width * bounding_box_height)

        # criterio robusto: una stanza riempie bene la sua bounding box
        # tra 0.5 e 0.6 -> una stanza deve riempire almeno la metà della box, i corridoi devono occupare meno
        # è una soglia naturale, è difficile che corridoi occupino più della metà
        if fill_ratio > 0.5:
            for (x, y) in cells:
                topo[y][x] = Topo.ROOM

    return topo, components

# Utility: conversione per visualizzazione nei file testuali
def topoToAscii(topo):
    rows = []

    for y in range(MAP_HEIGHT):
        row = []
        for x in range(MAP_WIDTH):
            t = topo[y][x]

            if t == Topo.ROOM:
                row.append('R')
            elif t == Topo.CORRIDOR:
                row.append('C')
            elif t == Topo.JUNCTION:
                row.append('J')
            elif t == Topo.DEADEND:
                row.append('D')
            else:
                row.append(' ')

        rows.append(''.join(row))

    return rows
