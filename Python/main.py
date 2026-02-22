import os

from algorithms.BSP import generate_bsp_dungeon
from algorithms.blind_agent import generate_agent_dungeon
from algorithms.look_ahead_agent import generate_lookahead_dungeon
from algorithms.cellular_automata import generate_cellular_dungeon
from algorithms.random_walk import generate_random_walk
from algorithms.maze_generation import generate_maze
from algorithms.hybrids.BSP_base.BSP_cellular import generate_bsp_cellular

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
        dungeon, rooms = generate_bsp_dungeon()
        save_map(dungeon, "bsp_" + str(i) + ".txt", "bsp")

        # Blind agent
        dungeon = generate_agent_dungeon()
        save_map(dungeon, "agent_blind_" + str(i) + ".txt", "blind_agent")

        # Look-ahead agent
        dungeon = generate_lookahead_dungeon()
        save_map(dungeon, "agent_lookahead_" + str(i) + ".txt", "lookahead_agent")

        # Cellular automata
        dungeon = generate_cellular_dungeon()
        save_map(dungeon, "cellular_automata_" + str(i) + ".txt", "cellular_automata")

        # Random walk
        dungeon = generate_random_walk()
        save_map(dungeon, "random_walk_" + str(i) + ".txt", "random_walk")

        # Maze generation
        dungeon = generate_maze()
        save_map(dungeon, "maze_" + str(i) + ".txt", "maze_generation")

        # Hybrid: BSP + Cellular
        dungeon = generate_bsp_cellular()
        save_map(dungeon, "bsp_cellular_" + str(i) + ".txt", path="bsp_cellular", default_alg=False)

    print("\nTutte le mappe sono state generate e salvate nella cartella 'maps/'.")
