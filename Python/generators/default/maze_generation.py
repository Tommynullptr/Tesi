import random

from Python.generators.terrain.terrain_CA import terrainToAscii
from Python.meta import MAZE_WIDTH, MAZE_HEIGHT, Terrain


# Depht-first search maze generation (recursive backtracking)
def generateMaze(maze_w=MAZE_WIDTH, maze_h=MAZE_HEIGHT, seed = None):
    if seed is None:
        seed = random.randint(0, 2**32 - 1)

    random.seed(seed)

    maze = [[Terrain.WALL for _ in range(maze_w)] for _ in range(maze_h)]

    def carve(x, y):
        maze[y][x] = Terrain.FLOOR
        dirs = [(2,0), (-2,0), (0,2), (0,-2)] # 2 perché scavo ogni 2 celle per lasciare un muro tra i corridoi
        random.shuffle(dirs)

        for dx, dy in dirs:
            new_x, new_y = x + dx, y + dy

            if 1 <= new_x < maze_w - 1 and 1 <= new_y < maze_h - 1:
                if maze[new_y][new_x] == Terrain.WALL:
                    maze[y + dy//2][x + dx//2] = Terrain.FLOOR
                    carve(new_x, new_y)

    carve(1, 1)

    ascii_map = terrainToAscii(maze)

    return ascii_map, seed