import statistics
from collections import deque

from Python.meta import Topo, Terrain


def has_object_at(objects, x, y):
    for obj in objects:
        if obj['x'] == x and obj['y'] == y:
            return True
    return False

def find_nearest_floor(dungeon, start, terrain, objects, max_radius=None):
    h = len(dungeon); w = len(dungeon[0])
    sx, sy = start
    if not (0 <= sx < w and 0 <= sy < h):
        return None
    # se lo start è già floor e non bloccato, restituiscilo
    if dungeon[sy][sx] == Terrain.FLOOR and terrain[sy][sx] != Terrain.WATER and not has_object_at(objects, sx, sy):
        return (sx, sy)
    q = deque([(sx, sy, 0)])
    visited = set([(sx, sy)])
    while q:
        x, y, d = q.popleft()
        if max_radius is not None and d > max_radius:
            break
        for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h and (nx, ny) not in visited:
                visited.add((nx, ny))
                if dungeon[ny][nx] == Terrain.FLOOR and terrain[ny][nx] != Terrain.WATER and not has_object_at(objects, nx, ny):
                    return (nx, ny)
                q.append((nx, ny, d + 1))
    return None

def compute_reachability_graph(dungeon, start_positions, objects, terrain):
    h = len(dungeon)
    w = len(dungeon[0])

    visited = [[False] * w for _ in range(h)]
    q = deque()

    # inizializza la coda con tutte le posizioni di start valide
    for (start_x, start_y) in start_positions:
        if 0 <= start_x < w and 0 <= start_y < h and dungeon[start_y][start_x] == Terrain.FLOOR and terrain[start_y][start_x] != Terrain.WATER and not has_object_at(objects, start_x, start_y):
            visited[start_y][start_x] = True
            q.append((start_x, start_y))

    # se non abbiamo start validi, prova a trovare il floor più vicino al primo start fornito
    if not q and start_positions:
        nearest = find_nearest_floor(dungeon, start_positions[0], terrain, objects, max_radius= 10)
        if nearest:
            sx, sy = nearest
            visited[sy][sx] = True
            q.append((sx, sy))

    reachable = 0

    while q:
        x, y = q.popleft()
        reachable += 1

        for direction_x, direction_y in [(-1,0),(1,0),(0,-1),(0,1)]:
            new_x, new_y = x + direction_x, y + direction_y

            if 0 <= new_x < w and 0 <= new_y < h:
                if (not visited[new_y][new_x] and dungeon[new_y][new_x] == Terrain.FLOOR and
                        terrain[new_y][new_x] != Terrain.WATER and not has_object_at(objects, new_x, new_y)):
                    visited[new_y][new_x] = True
                    q.append((new_x, new_y))

    return reachable

def compute_basic_feature_vector(dungeon, topo, components, rooms, terrain, objects, config, maze = False):
    feat_dict = {} # dizionario di features

    if maze:
        map_height = config["maze_height"]
        map_width = config["maze_width"]
    else:
        map_height = config["map_height"]
        map_width = config["map_width"]

    # 1) FRAZIONE DI PAVIMENTO, quanto floor ho
    floor_cells = sum(
        1 for y in range(map_height)
        for x in range(map_width)
        if dungeon[y][x] == Terrain.FLOOR
    )
    feat_dict["floor_fraction"] = floor_cells / (map_width * map_height) # percentuale di pavimento rispetto alla mappa intera

    # 2) STATISTICHE DELLE STANZE (components)
    sizes = [len(c) for c in rooms] if rooms else []

    if sizes:
        feat_dict["room_count"] = len(sizes)
        feat_dict["avg_room_size"] = sum(sizes) / len(sizes)
        feat_dict["max_room_size"] = max(sizes)
    else:
        feat_dict["room_count"] = 0
        feat_dict["avg_room_size"] = 0
        feat_dict["max_room_size"] = 0

    # 3) LAGHI (celle WATER nel terrain)
    lakes = []
    visited = [[False] * map_width for _ in range(map_height)]

    for y in range(map_height):
        for x in range(map_width):

            if terrain[y][x] == Terrain.WATER and not visited[y][x]:

                q = deque([(x,y)]) # bfs per celle d'acqua vicine
                visited[y][x] = True
                size = 0

                while q:
                    cx, cy = q.popleft()
                    size += 1

                    for direction_x, direction_y in [(-1,0),(1,0),(0,-1),(0,1)]:
                        new_x, new_y = cx + direction_x, cy + direction_y

                        if 0 <= new_x < map_width and 0 <= new_y < map_height:
                            if not visited[new_y][new_x] and terrain[new_y][new_x] == Terrain.WATER:
                                visited[new_y][new_x] = True
                                q.append((new_x, new_y))

                lakes.append(size)

    feat_dict["lake_count"] = len(lakes)
    feat_dict["avg_lake_size"] = sum(lakes)/len(lakes) if lakes else 0

    # 4) DEAD-ENDS
    deadends = 0

    for y in range(map_height):
        for x in range(map_width):
            if topo[y][x] == Topo.DEADEND:
                deadends += 1

    feat_dict["deadend_count"] = deadends

    # 5) CORRIDORS quantità di corridoi
    corridors = 0

    for y in range(map_height):
        for x in range(map_width):
            if topo[y][x] == Topo.CORRIDOR:
                corridors += 1

    feat_dict["corridor_count"] = corridors
    feat_dict["corridor_fraction"] = corridors / floor_cells if floor_cells > 0 else 0

    # 6) OGGETTI
    object_count = len(objects)
    feat_dict["object_count"] = object_count
    feat_dict["object_density"] = object_count / floor_cells if floor_cells > 0 else 0

    return feat_dict

# come impatta il parametro sulla feature?
def record_controllability(m, param_name, param_value, feature_name):
    feature_value = m.features["feature_vector"][feature_name]
    m.record_control_sample(param_name, param_value, feature_value)


def post_process_measures(m, config, maze = False):
    # ATTENZIONE: aggiungere a meta la roba che serve qui nei generatori
    dungeon = m.meta["dungeon"]
    topo = m.meta["topo"]
    components = m.meta["components"]
    terrain = m.meta["terrain"]
    objects = m.meta["objects"]
    rooms = m.meta["rooms"]

    # --- EXPRESSIVITY / DIVERSITY ---
    feat_dict = compute_basic_feature_vector(dungeon, topo, components, rooms, terrain, objects, config, maze = maze)
    m.set_features_vector(feat_dict)

    # --- RELIABILITY ---
    # celle raggiungibili considerando oggetti e terreni considerati bloccanti
    reachable = compute_reachability_graph(dungeon, [config["start"], (1, 1)], objects, terrain)
    m.add_feature("reachable_from_start", reachable)

    # --- SENSITIVITY / CONTROLLABILITY ---
    # Calcola sensitivities per tutti i parametri per cui abbiamo samples
    for param in list(m.sensitivity_data.keys()):
        # compute_sensitivity aggiunge la feature "<param>_sens" dentro m.features
        m.compute_sensitivity(param)

    # Aggiungi riepilogo delle sensitivities (mean, max, min) se presenti
    sens_keys = [k for k in m.features.keys() if k.endswith("_sens")]
    if sens_keys:
        sens_vals = [float(m.features[k]) for k in sens_keys]
        m.add_feature("sensitivity_count", len(sens_vals))
        m.add_feature("sensitivity_mean", statistics.mean(sens_vals))
        m.add_feature("sensitivity_max", max(sens_vals))
        m.add_feature("sensitivity_min", min(sens_vals))

    # Salva info di coverage dei parametri (già aggiornate da record_control_sample)
    # e copia in features per serializzazione/analisi rapida
    for pname, cov in m.control_coverage.items():
        m.add_feature(f"coverage_{pname}_min", cov.get("min"))
        m.add_feature(f"coverage_{pname}_max", cov.get("max"))
        m.add_feature(f"coverage_{pname}_unique", cov.get("unique"))
