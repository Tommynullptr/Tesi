import random

from Python.meta import MAP_WIDTH, MAP_HEIGHT, Terrain, Topo

# Object placement avoiding corridors
def placeObjectsOnTerrain(terrain, topo, seed=None, params=None):
    """
    Place trees on GRASS and rocks on WATER.
    Avoid placing objects on TOPO_CORRIDOR or TOPO_DEADEND (configurable).
    Use coarse occupancy grid for spacing.
    """
    rng = random.Random(seed)

    if params is None:
        params = {'p_tree':0.04, 'p_rock':0.01, 'avoid_topo': {Topo.CORRIDOR, Topo.DEADEND}, 'cell_spacing':3}

    cell_size = max(1, params['cell_spacing'])
    grid_w = (MAP_WIDTH + cell_size - 1)//cell_size
    grid_h = (MAP_HEIGHT + cell_size - 1)//cell_size
    occ = [[None]*grid_w for _ in range(grid_h)]
    objects = []

    def grid_coords(x,y):
        return x//cell_size, y//cell_size

    for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):
            t = terrain[y][x]
            topo_val = topo[y][x]

            if topo_val in params['avoid_topo']: continue

            gx, gy = grid_coords(x,y)

            if t == Terrain.GRASS and rng.random() < params['p_tree']:
                # check local occupancy
                nearby = False

                for ix in range(max(0,gx-1), min(grid_w, gx+2)):
                    for iy in range(max(0,gy-1), min(grid_h, gy+2)):

                        if occ[iy][ix] is not None:
                            nearby = True; break

                    if nearby: break

                if not nearby:
                    occ[gy][gx] = ('tree', x, y)
                    objects.append({'x':x,'y':y,'type':'tree'})

            if t == Terrain.WATER and rng.random() < params['p_rock']:
                if occ[gy][gx] is None:

                    occ[gy][gx] = ('rock', x, y)
                    objects.append({'x':x,'y':y,'type':'rock'})

    return objects