from Python.algorithms.BSP import generate_bsp_dungeon
from Python.algorithms.cellular_automata import generate_cellular_dungeon
from Python.meta import MAP_WIDTH, MAP_HEIGHT


def generate_bsp_cellular():
    # TODO: i corridoi tra le stanze possono essere bloccati dalla cellular automata
    dungeon, rooms = generate_bsp_dungeon()

    # utilizzo rooms per applicare ad ogni stanza
    # la cellular automata
    for room in rooms:
        room_x, room_y, room_w, room_h = room # room_x & room_y = top-left

        cellular_room = generate_cellular_dungeon(room_w, room_h)

        # Disegna la cellular_room nel dungeon BSP
        for y in range(room_h):
            for x in range(room_w):
                if cellular_room[y][x] == "#":
                    new_x = room_x + x
                    new_y = room_y + y
                    if 0 <= new_x < MAP_WIDTH and 0 <= new_y < MAP_HEIGHT:
                        dungeon[new_y][new_x] = "#"

    return dungeon
