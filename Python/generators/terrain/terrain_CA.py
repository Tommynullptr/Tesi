import random

from Python.meta import Terrain, Topo


# CA per generare terreno su un dungeon scavato
def terrain_CA_from_dungeon(dungeon, topo, components, config, seed = None, maze = False,
                            prob_lake = 0.06, lake_fraction = 0.12, water_spread_threshold = 3,
                            grass_spread_threshold = 1, grass_near_water_prob = 0.9, grass_near_grass_prob = 0.4):
    """
    Output: matrice/layer della mappa con GROUND/GRASS/WATER (terra/erba/acqua).
    Strategia:
      - semina laghi nelle componenti topologiche TOPO_ROOM con probabilità prob_lake
      - espandi l'acqua secondo la regola locale: a floor cell becomes water if >= water_spread_threshold water neighbors
      - l'erba si può propagare vicino all'acqua o ad altre celle di erba
    """
    rng = random.Random(seed)
    
    if maze:
        map_w = config["maze_width"]
        map_h = config["maze_height"]
    else:
        map_w = config["map_width"]
        map_h = config["map_height"]
    
    terrain = [[Terrain.WALL if dungeon[y][x] == Terrain.WALL else Terrain.FLOOR for x in range(map_w)]
               for y in range(map_h)]

    # macchie di ground casuali su cui può crescere erba + propagazione
    for y in range(map_h):
        for x in range(map_w):

            if dungeon[y][x] == Terrain.FLOOR and rng.random() < 0.1:
                terrain[y][x] = Terrain.GROUND

    for _ in range(2):
        new_terrain = [row[:] for row in terrain]

        for y in range(map_h):
            for x in range(map_w):
                for direction_x,direction_y in [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(1,1),(-1,1),(1,-1)]:
                    new_x, new_y = x+direction_x, y+direction_y

                    if 0 <= new_x < map_w and 0 <= new_y < map_h:
                        if terrain[new_y][new_x] == Terrain.GROUND and rng.random() < 0.2:
                            new_terrain[y][x] = Terrain.GROUND

        terrain = new_terrain

    # semina laghi in stanze grandi
    for cells in components.values():
        if len(cells) < config["min_room_size_for_lake"]: continue # piazza laghi solo in componenti abbastanza grandi

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
                    
                    if 0 <= new_x < map_w and 0 <= new_y < map_h and dungeon[new_y][new_x] == Terrain.FLOOR and (new_x,new_y) in cells:
                        if rng.random() < 0.6:
                            lake.add((new_x,new_y)); frontier.append((new_x,new_y))
                            
            for (lx,ly) in lake:
                terrain[ly][lx] = Terrain.WATER

    # propagazione acqua: una cella di pavimento diventa acqua se ha abbastanza vicini acqua (regola locale)
    # con poche iterazioni per evitare di allagare tutto
    # l'acqua non deve propagarsi vicino ai muri o ai corridoi per non bloccare la mappa
    for _ in range(3):
        new_terrain = [row[:] for row in terrain]

        for y in range(map_h):
            for x in range(map_w):

                if dungeon[y][x] == Terrain.FLOOR and terrain[y][x] != Terrain.WATER:
                    water_neighbors = 0
                    near_wall_or_corridor = False

                    for direction_x,direction_y in [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(1,1),(-1,1),(1,-1)]:
                        new_x, new_y = x+direction_x, y+direction_y

                        if 0 <= new_x < map_w and 0 <= new_y < map_h:
                            if terrain[new_y][new_x] == Terrain.WATER:
                                water_neighbors += 1

                            if dungeon[new_y][new_x] == Terrain.WALL or topo[new_y][new_x] == Topo.CORRIDOR:
                                near_wall_or_corridor = True
                                break

                    if (water_neighbors >= water_spread_threshold and rng.random() < 0.9 and
                            topo[y][x] != Topo.CORRIDOR and not near_wall_or_corridor):
                        new_terrain[y][x] = Terrain.WATER

        terrain = new_terrain

    # macchie di erba per variare la mappa e introdurre rumore per generare macchie più grandi di erba
    for y in range(map_h):
        for x in range(map_w):

            if dungeon[y][x] == Terrain.FLOOR and terrain[y][x] == Terrain.GROUND and rng.random() < 0.15:
                terrain[y][x] = Terrain.GRASS

    # propagazione erba: preferisce crescere vicino all'acqua, ma può anche diffondersi per vicinanza ad altre celle d'erba
    for _ in range(2):
        new_terrain = [row[:] for row in terrain]

        for y in range(map_h):
            for x in range(map_w):

                if dungeon[y][x] == Terrain.FLOOR and terrain[y][x] == Terrain.GROUND:
                    # conta vicini acqua e erba per decidere se diventare erba
                    water_n = 0; grass_n = 0

                    for direction_x,direction_y in [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(1,1),(-1,1),(1,-1)]:
                        new_x, new_y = x+direction_x, y+direction_y

                        if 0 <= new_x < map_w and 0 <= new_y < map_h:

                            if terrain[new_y][new_x] == Terrain.WATER: water_n += 1
                            if terrain[new_y][new_x] == Terrain.GRASS: grass_n += 1

                    if water_n > 0 and rng.random() < grass_near_water_prob:
                        new_terrain[y][x] = Terrain.GRASS

                    elif grass_n >= grass_spread_threshold and rng.random() < grass_near_grass_prob:
                        new_terrain[y][x] = Terrain.GRASS

        terrain = new_terrain

    return terrain

# Utility: conversione per visualizzazione nei file testuali
def terrain_to_ascii(dungeon, terrain, objects, config, maze = False):

    if maze:
        map_w = config["maze_width"]
        map_h = config["maze_height"]
    else:
        map_w = config["map_width"]
        map_h = config["map_height"]

    obj_map = {(o['x'],o['y']): o['type'][0].upper() for o in (objects or [])}
    rows = []

    for y in range(map_h):
        row = []

        for x in range(map_w):
            if (x,y) in obj_map:
                row.append(obj_map[(x,y)])

            else:
                if dungeon[y][x] == Terrain.WALL:
                    row.append('#')

                else:
                    t = None if terrain is None else terrain[y][x]

                    if t == Terrain.WATER: row.append('~')
                    elif t == Terrain.GRASS: row.append('"')
                    elif t == Terrain.GROUND: row.append('_')
                    else: row.append('.')

        rows.append(''.join(row))

    return rows
