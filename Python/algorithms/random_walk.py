import random
from Python.meta import MAP_WIDTH, MAP_HEIGHT, TARGET_FLOOR

def generate_random_walk():
    
    dungeon = [["#" for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]

    x = MAP_WIDTH // 2
    y = MAP_HEIGHT // 2

    directions = [(1,0), (-1,0), (0,1), (0,-1)]
    dug = 0

    while dug < TARGET_FLOOR:
        dungeon[y][x] = "."
        dug += 1

        dx, dy = random.choice(directions)
        x = max(1, min(MAP_WIDTH - 2, x + dx))
        y = max(1, min(MAP_HEIGHT - 2, y + dy))

    return dungeon

# TODO: versione che non torna sulle stesse celle
