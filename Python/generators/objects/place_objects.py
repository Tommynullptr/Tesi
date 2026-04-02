import random

from Python.meta import Terrain, Topo


def place_objects_on_terrain(terrain, topo, config, seed=None, params=None, maze = False):
    """
    Piazza alberi su erba e rocce/scogli su acqua.
    Evita di piazzare oggeti su corridoi e deadend.
    Possibilità di piazzare tesori su deadend
    Utilizza occupancy grid per lo spacing tra oggetti.
    """
    rng = random.Random(seed)
    
    if maze:
        map_w = config["maze_width"]
        map_h = config["maze_height"]
    else:
        map_w = config["map_width"]
        map_h = config["map_height"]

    if params is None:
        params = {'prob_tree': 0.15, 'prob_rock': 0.05, 'prob_chest': 0.1,
                  'rock_spacing': 3, 'tree_spacing': 1}

    # grid per gli alberi
    tree_cell_size = max(1, params['tree_spacing'])
    tree_grid_width = (map_w + tree_cell_size - 1) // tree_cell_size
    tree_grid_height = (map_h + tree_cell_size - 1) // tree_cell_size
    tree_occurrency = [[None] * tree_grid_width for _ in range(tree_grid_height)]

    # grid per le rocce
    rock_cell_size = max(1, params['rock_spacing'])
    rock_grid_width = (map_w + rock_cell_size - 1) // rock_cell_size
    rock_grid_height = (map_h + rock_cell_size - 1) // rock_cell_size
    rock_occurrency = [[None] * rock_grid_width for _ in range(rock_grid_height)]

    objects = []

    def grid_coords(x,y, cell_size):
        return x // cell_size, y // cell_size

    def nearby_corridor(x, y):
        for direction_x, direction_y in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            new_x, new_y = x + direction_x, y + direction_y

            if 0 <= new_x < map_w and 0 <= new_y < map_h:
                if topo[new_y][new_x] == Topo.CORRIDOR:
                    return True

        return False

    for y in range(map_h):
        for x in range(map_w):
            
            t = terrain[y][x]
            topo_val = topo[y][x]

            # chest nei deadend
            if topo_val == Topo.DEADEND and rng.random() < params['prob_chest']:
                objects.append({'x': x, 'y': y, 'type': 'chest'})
                continue

            if topo_val == Topo.CORRIDOR: continue

            tree_grid_x, tree_grid_y = grid_coords(x, y, tree_cell_size)
            rock_grid_x, rock_grid_y = grid_coords(x, y, rock_cell_size)

            if t == Terrain.GRASS and rng.random() < params['prob_tree']:
                # check local occupancy
                nearby = False

                for ix in range(max(0,tree_grid_x - 1), min(tree_grid_width, tree_grid_x + 2)):
                    for iy in range(max(0,tree_grid_y - 1), min(tree_grid_height, tree_grid_y + 2)):

                        if tree_occurrency[iy][ix] is not None:
                            nearby = True; break

                    if nearby: break

                if not nearby and not nearby_corridor(x, y):
                    tree_occurrency[tree_grid_y][tree_grid_x] = ('tree', x, y)
                    objects.append({'x':x,'y':y,'type':'tree'})

            if t == Terrain.WATER and rng.random() < params['prob_rock']:
                if rock_occurrency[rock_grid_y][rock_grid_x] is None:

                    rock_occurrency[rock_grid_y][rock_grid_x] = ('rock', x, y)
                    objects.append({'x':x,'y':y,'type':'rock'})

    return objects