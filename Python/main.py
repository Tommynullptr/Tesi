import os

from Python.generators.default.BSP import generateBspDungeon
from Python.generators.default.blind_agent import generateBlindDungeon
from Python.generators.default.look_ahead_agent import generateLookaheadDungeon
from Python.generators.default.cellular_automata import generateCellularDungeon
from Python.generators.default.random_walk import generateRandomWalk
from Python.generators.default.maze_generation import generateMaze
from meta import MAPS_AMOUNT


# Salva la mappa nella cartella "maps/" con il nome specificato
def save_map(dungeon, filename, path = "none", default_alg = True):
    
    base_path = "Python\maps"
        
    default_path = os.path.join(base_path, "default")
    hybrids_path = os.path.join(base_path, "hybrids")
    
    if path != "none" and default_alg:
        default_path = os.path.join(default_path, path)
    else: 
        hybrids_path = os.path.join(hybrids_path, path)

    os.makedirs(default_path, exist_ok=True)
    os.makedirs(hybrids_path, exist_ok=True)

    if default_alg:
        full_path = os.path.join(default_path, filename)
    else:
        full_path = os.path.join(hybrids_path, filename)

    with open(full_path, "w") as f:
        for row in dungeon:
            f.write("".join(row) + "\n")

    print(f"✔ Mappa salvata in {full_path}")


if __name__ == "__main__":
    for i in range(MAPS_AMOUNT):

        # BSP
        dungeon, rooms, seed, topo = generateBspDungeon()
        save_map(dungeon, "bsp_" + str(seed) + ".txt", "bsp")
        save_map(topo, "bsp_topo_" + str(seed) + ".txt", "bsp")

        # Blind agent
        dungeon, seed, topo = generateBlindDungeon()
        save_map(dungeon, "agent_blind_" + str(seed) + ".txt", "blind_agent")
        save_map(topo, "agent_blind_topo_" + str(seed) + ".txt", "blind_agent")

        # Look-ahead agent
        dungeon, seed, topo = generateLookaheadDungeon()
        save_map(dungeon, "agent_lookahead_" + str(seed) + ".txt", "lookahead_agent")
        save_map(topo, "agent_lookahead_topo_" + str(seed) + ".txt", "lookahead_agent")

        # Cellular automata
        dungeon, seed, topo = generateCellularDungeon()
        save_map(dungeon, "cellular_automata_" + str(seed) + ".txt", "cellular_automata")
        save_map(topo, "cellular_automata_topo_" + str(seed) + ".txt", "cellular_automata")

        # Random walk
        dungeon, seed, topo = generateRandomWalk()
        save_map(dungeon, "random_walk_" + str(seed) + ".txt", "random_walk")
        save_map(topo, "random_walk_topo_" + str(seed) + ".txt", "random_walk")

        # Maze generation
        dungeon, seed = generateMaze()
        save_map(dungeon, "maze_" + str(seed) + ".txt", "maze_generation")

        """
        # Hybrid: BSP + Cellular
        dungeon = generateBspCellular()
        save_map(dungeon, "bsp_cellular_" + str(i) + ".txt", path="bsp_cellular", default_alg=False)

        # Hybrid: BSP + Maze
        dungeon = generateBspMaze()
        save_map(dungeon, "bsp_maze_" + str(i) + ".txt", path="bsp_maze", default_alg=False)

        # Hybrid: Maze + Cellular
        # utilizza il bsp quindi sfrutta il metodo generate_bsp_cellular
        dungeon = generateMazeCellular()
        save_map(dungeon, "maze_cellular_" + str(i) + ".txt", path="maze_cellular", default_alg=False)
        """

    print("\nTutte le mappe sono state generate e salvate nella cartella 'maps/'.")
