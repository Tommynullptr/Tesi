import random

from Python.meta import MAP_WIDTH, MAP_HEIGHT, Terrain, Topo


def placeObjectsOnTerrain(terrain, topo, seed=None, params=None):
    """
    Piazza alberi su erba e rocce/scogli su acqua.
    Evita di piazzare oggeti su corridoi e deadend.
    Possibilità di piazzare tesori su deadend
    Utilizza occupancy grid per lo spacing tra oggetti.
    """
    rng = random.Random(seed)

    if params is None:
        params = {'prob_tree': 0.15, 'prob_rock': 0.05, 'prob_chest': 0.1,
                  'rock_spacing': 3, 'tree_spacing': 1}

    # grid per gli alberi
    tree_cell_size = max(1, params['tree_spacing'])
    tree_grid_width = (MAP_WIDTH + tree_cell_size - 1) // tree_cell_size
    tree_grid_height = (MAP_HEIGHT + tree_cell_size - 1) // tree_cell_size
    tree_occurrency = [[None] * tree_grid_width for _ in range(tree_grid_height)]

    # grid per le rocce
    rock_cell_size = max(1, params['rock_spacing'])
    rock_grid_width = (MAP_WIDTH + rock_cell_size - 1) // rock_cell_size
    rock_grid_height = (MAP_HEIGHT + rock_cell_size - 1) // rock_cell_size
    rock_occurrency = [[None] * rock_grid_width for _ in range(rock_grid_height)]

    objects = []

    def grid_coords(x,y, cell_size):
        return x // cell_size, y // cell_size

    def nearbyCorridor(x, y):
        for direction_x, direction_y in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            new_x, new_y = x + direction_x, y + direction_y

            if 0 <= new_x < MAP_WIDTH and 0 <= new_y < MAP_HEIGHT:
                if topo[new_y][new_x] == Topo.CORRIDOR:
                    return True

        return False

    for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):
            
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

                if not nearby and not nearbyCorridor(x, y):
                    tree_occurrency[tree_grid_y][tree_grid_x] = ('tree', x, y)
                    objects.append({'x':x,'y':y,'type':'tree'})

            if t == Terrain.WATER and rng.random() < params['prob_rock']:
                if rock_occurrency[rock_grid_y][rock_grid_x] is None:

                    rock_occurrency[rock_grid_y][rock_grid_x] = ('rock', x, y)
                    objects.append({'x':x,'y':y,'type':'rock'})

    return objects