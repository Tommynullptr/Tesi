from Python.generators.default.maze_generation import generate_maze
from Python.generators.hybrids.BSP_base.BSP_cellular import generateBspCellular


def generateMazeCellular():
    # TODO: i corridoi tra le stanze possono essere bloccati dalla cellular automata
    dungeon = generate_maze()

    dungeon = generateBspCellular(dungeon)

    return dungeon