import random
from Python.meta import MAZE_WIDTH, MAZE_HEIGHT

# Depht-first search maze generation (recursive backtracking)
def generate_maze():

    maze = [["#" for _ in range(MAZE_WIDTH)] for _ in range(MAZE_HEIGHT)]

    def carve(x, y):

        maze[y][x] = "."
        dirs = [(2,0), (-2,0), (0,2), (0,-2)] # 2 perché scavo ogni 2 celle per lasciare un muro tra i corridoi
        random.shuffle(dirs)

        for dx, dy in dirs:
            new_x, new_y = x + dx, y + dy

            if 1 <= new_x < MAZE_WIDTH - 1 and 1 <= new_y < MAZE_HEIGHT - 1:
                if maze[new_y][new_x] == "#":
                    maze[y + dy//2][x + dx//2] = "."
                    carve(new_x, new_y)

    carve(1, 1)
    return maze