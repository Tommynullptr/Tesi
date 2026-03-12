import random

from Python.generators.terrain.terrain_CA import terrainCAFromDungeon, terrainToAscii
from Python.generators.objects.place_objects import placeObjectsOnTerrain
from Python.generators.topology.classify_cells import classifyCells, topoToAscii
from Python.meta import MAP_WIDTH, MAP_HEIGHT, TARGET_FLOOR, Terrain, START


def generateRandomWalk(seed = None):
    if seed is None:
        seed = random.randint(0, 2**32 - 1)

    random.seed(seed)
    
    dungeon = [[Terrain.WALL for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]

    x, y = START
    directions = [(1,0), (-1,0), (0,1), (0,-1)]
    dug = 0

    while dug < TARGET_FLOOR:
        dungeon[y][x] = Terrain.FLOOR
        dug += 1

        dx, dy = random.choice(directions)
        x = max(1, min(MAP_WIDTH - 2, x + dx))
        y = max(1, min(MAP_HEIGHT - 2, y + dy))

    topo, components = classifyCells(dungeon)
    terrain = terrainCAFromDungeon(dungeon, topo, components, seed = seed)
    objects = placeObjectsOnTerrain(terrain, topo)
    ascii_map = terrainToAscii(dungeon, terrain, objects)
    ascii_topo = topoToAscii(topo)

    return ascii_map, seed, ascii_topo

# TODO: versione che non torna sulle stesse celle
