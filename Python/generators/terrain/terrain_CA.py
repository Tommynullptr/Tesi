import random

from collections import deque
from Python.meta import MAP_WIDTH, MAP_HEIGHT, Terrain, MIN_ROOM_SIZE_FOR_LAKE, Topo


# CA per generare terreno su un dungeon scavato
def terrainCAFromDungeon(dungeon, topo, components, seed=None,
                         prob_lake=0.06, lake_fraction=0.12, water_spread_threshold=3,
                         grass_spread_threshold=2, grass_near_water_prob=0.9):
    """
    Output: matrice/layer della mappa con GROUND/GRASS/WATER (terra/erba/acqua).
    Strategia:
      - semina laghi nelle componenti topologiche TOPO_ROOM con probabilità prob_lake
      - espandi l'acqua secondo la regola locale: a floor cell becomes water if >= water_spread_threshold water neighbors
      - l'erba si può propagare vicino all'acqua o ad altre celle di erba
    """
    rng = random.Random(seed)
    terrain = [[Terrain.WALL if dungeon[y][x] == Terrain.WALL else Terrain.GROUND for x in range(MAP_WIDTH)] for y in range(MAP_HEIGHT)]

    # semina laghi in stanze grandi
    for cells in components.values():
        if len(cells) < MIN_ROOM_SIZE_FOR_LAKE: continue # piazza laghi solo in componenti abbastanza grandi

        if rng.random() < prob_lake:
            target_len = max(1, int(len(cells) * min(lake_fraction, 0.03 + rng.random()*0.12)))
            seed_cell = rng.choice(cells)
            lake = set([seed_cell]) # usa un set per evitare duplicati e per check O(1) di appartenenza
            frontier = [seed_cell] # lista di celle ai bordi del lago da cui espandere; inizia con la cella seed
            
            while frontier and len(lake) < target_len:
                cell_x, cell_y = frontier.pop(rng.randrange(len(frontier)))
                
                for direction_x,direction_y in [(-1,0),(1,0),(0,-1),(0,1)]:
                    new_x, new_y = cell_x + direction_x, cell_y + direction_y
                    
                    if (new_x,new_y) in lake: continue
                    
                    if 0 <= new_x < MAP_WIDTH and 0 <= new_y < MAP_HEIGHT and dungeon[new_y][new_x] == Terrain.FLOOR and (new_x,new_y) in cells:
                        if rng.random() < 0.6:
                            lake.add((new_x,new_y)); frontier.append((new_x,new_y))
                            
            for (lx,ly) in lake:
                terrain[ly][lx] = Terrain.WATER

    # propagazione acqua: una cella di pavimento diventa acqua se ha abbastanza vicini acqua (regola locale)
    # con poche iterazioni per evitare di coprire troppo
    for _ in range(3):
        new_terrain = [row[:] for row in terrain]

        for y in range(MAP_HEIGHT):
            for x in range(MAP_WIDTH):

                if dungeon[y][x] == Terrain.FLOOR and terrain[y][x] != Terrain.WATER:
                    water_neighbors = 0

                    for direction_x,direction_y in [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(1,1),(-1,1),(1,-1)]:
                        new_x, new_y = x+direction_x, y+direction_y

                        if 0 <= new_x < MAP_WIDTH and 0 <= new_y < MAP_HEIGHT and terrain[new_y][new_x] == Terrain.WATER:
                            water_neighbors += 1

                    if water_neighbors >= water_spread_threshold and rng.random() < 0.9:
                        new_terrain[y][x] = Terrain.WATER

        terrain = new_terrain

    # propagazione erba: preferisce crescere vicino all'acqua, ma può anche diffondersi per vicinanza ad altre celle d'erba
    # TODO: aumentare la fittosità dell'erba
    for _ in range(2):
        new_terrain = [row[:] for row in terrain]

        for y in range(MAP_HEIGHT):
            for x in range(MAP_WIDTH):

                if dungeon[y][x] == Terrain.FLOOR and terrain[y][x] == Terrain.GROUND:
                    # conta vicini acqua e erba per decidere se diventare erba
                    water_n = 0; grass_n = 0

                    for direction_x,direction_y in [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(1,1),(-1,1),(1,-1)]:
                        new_x, new_y = x+direction_x, y+direction_y

                        if 0 <= new_x < MAP_WIDTH and 0 <= new_y < MAP_HEIGHT:

                            if terrain[new_y][new_x] == Terrain.WATER: water_n += 1
                            if terrain[new_y][new_x] == Terrain.GRASS: grass_n += 1

                    if water_n > 0 and rng.random() < grass_near_water_prob:
                        new_terrain[y][x] = Terrain.GRASS

                    elif grass_n >= grass_spread_threshold:
                        new_terrain[y][x] = Terrain.GRASS

        terrain = new_terrain

    # macchie di erba per variare la mappa
    for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):

            if dungeon[y][x] == Terrain.FLOOR and terrain[y][x] == Terrain.GROUND and rng.random() < 0.01:
                terrain[y][x] = Terrain.GRASS

    return terrain

# Utility: conversione per visualizzazione nei file testuali
def terrainToAscii(dungeon, terrain = None, objects=None):

    obj_map = {(o['x'],o['y']): o['type'][0].upper() for o in (objects or [])}
    rows = []

    for y in range(MAP_HEIGHT):
        row = []

        for x in range(MAP_WIDTH):
            if (x,y) in obj_map:
                row.append(obj_map[(x,y)])

            else:
                if dungeon[y][x] == Terrain.WALL:
                    row.append('#')

                else:
                    t = None if terrain is None else terrain[y][x]

                    if t == Terrain.WATER: row.append('~')
                    elif t == Terrain.GRASS: row.append('"')
                    else: row.append('.')

        rows.append(''.join(row))

    return rows
