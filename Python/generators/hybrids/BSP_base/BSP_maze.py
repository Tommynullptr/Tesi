from Python.generators.default.BSP import generateBspDungeon
from Python.generators.default.maze_generation import generateMaze
from Python.meta import MAP_WIDTH, MAP_HEIGHT

import random


def generateBspMaze():
    # TODO: i corridoi tra le stanze possono essere bloccati dalla cellular automata
    dungeon, rooms = generateBspDungeon()

    # utilizzo rooms per applicare ad ogni stanza
    # la cellular automata
    for room in rooms:
        if random.choice([True, False]): # solo alcune stanze sono labirinti
            continue

        room_x, room_y, room_w, room_h = room # room_x & room_y = top-left

        maze_room = generateMaze(room_w, room_h)

        # Disegna la cellular_room nel dungeon BSP
        for y in range(room_h):
            for x in range(room_w):
                if maze_room[y][x] == "#":
                    new_x = room_x + x
                    new_y = room_y + y
                    if 0 <= new_x < MAP_WIDTH and 0 <= new_y < MAP_HEIGHT:
                        dungeon[new_y][new_x] = "#"

    return dungeon