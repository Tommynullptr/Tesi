from Python.generators.default.maze_generation import generateMaze
from Python.generators.hybrids.BSP_base.BSP_cellular import generateBspCellular


def generateMazeCellular():
    # TODO: i corridoi tra le stanze possono essere bloccati dalla cellular automata
    dungeon = generateMaze()

    dungeon = generateBspCellular(dungeon)

    return dungeon