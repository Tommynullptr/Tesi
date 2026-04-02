import os
import random
from collections import defaultdict

from Python.generators.default.BSP import generate_bsp_dungeon
from Python.generators.default.blind_agent import generate_blind_dungeon
from Python.generators.default.look_ahead_agent import generate_lookahead_dungeon
from Python.generators.default.cellular_automata import generate_cellular_dungeon
from Python.generators.default.random_walk import generate_random_walk
from Python.generators.default.maze_generation import generate_maze
from Python.measures.measures import Measures
from Python.measures.postprocess import record_controllability
from meta import MAPS_AMOUNT


def build_agg_from_samples(label, samples_dict):
    """
    Crea un Measures aggregato per un generatore.
    samples_dict: dict param_name -> list of (param_value, feature_value)
    Ritorna l'oggetto Measures popolato (con sensitivity_data e control_coverage).
    """
    agg = Measures(seed=None, label=f"sensitivity_agg_{label}", input_params = None)

    # trasferisci solo parametri con almeno 2 campioni
    for pname, samples in samples_dict.items():
        if len(samples) < 2:
            print(f"⚠ {label}: skip {pname}, only {len(samples)} samples")
            continue
        agg.sensitivity_data[pname] = [(float(x), float(y)) for x, y in samples]
        vals = [v for v, _ in agg.sensitivity_data[pname]]
        agg.control_coverage[pname] = {"min": min(vals), "max": max(vals), "unique": len(set(vals))}

    # calcola sensitivities per ogni parametro trasferito
    computed = {}
    for pname in list(agg.sensitivity_data.keys()):
        res = agg.compute_sensitivity(pname)
        computed[pname] = res
        print(f"{label}: compute_sensitivity {pname} -> {res}")

    return agg, computed

# Salva la mappa nella cartella "maps/" con il nome specificato
def saveMap(dungeon, filename, path ="none", default_alg = True):
    
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
    measures_list = []
    global_sensitivity = defaultdict(list)

    for i in range(MAPS_AMOUNT):

        min_node_size = random.randint(4, 12)
        max_node_size = random.randint(15, 40)
        map_width = random.randint(40, 400)
        map_height = random.randint(40, 400)
        prob_corridor = random.randint(5, 15)
        prob_room = random.randint(5, 15)
        min_room_size = random.randint(4, 9)
        max_room_size = random.randint(12, 25)
        min_corridor_size = random.randint(4,8)
        max_corridor_size = random.randint(15, 35)
        initial_chance = random.uniform(0.40, 0.48)
        iterations = random.randint(3, 5)
        num_of_walls = random.randint(4, 5)
        maze_width = random.randrange(41, 201, 2)  # dispari
        maze_height = random.randrange(41, 201, 2)  # dispari
        min_room_size_for_lake = random.randint(10, 35)
        target_floor = random.randint((map_width * map_height) // 4, (map_width * map_height))

        config = {
            "min_node_size": min_node_size,
            "max_node_size": max_node_size,
            "map_width": map_width,
            "map_height": map_height,
            "prob_corridor": prob_corridor,
            "prob_room": prob_room,
            "min_room_size": min_room_size,
            "max_room_size": max_room_size,
            "start": (map_width // 2, map_height // 2),
            "target_floor": target_floor,
            "min_corridor_size": min_corridor_size,
            "max_corridor_size": max_corridor_size,
            "initial_chance": initial_chance,
            "iterations": iterations,
            "num_of_walls": num_of_walls,
            "maze_width": maze_width,
            "maze_height": maze_height,
            "min_room_size_for_lake": min_room_size_for_lake
        }

        # ------ BSP ------
        dungeon, rooms, seed, topo, measures = generate_bsp_dungeon(config)
        measures_list.append(measures)
        saveMap(dungeon, "bsp_" + str(seed) + ".txt", "bsp")
        saveMap(topo, "bsp_topo_" + str(seed) + ".txt", "bsp")
        measures.to_json(f"Python/results/bsp_jsons/bsp_{seed}.json")

        # dopo che 'measures' è stato prodotto e post_process_measures è stato eseguito
        # registra campioni per la controllabilità (per run singolo)
        # usa record_controllability per popolare m.sensitivity_data
        record_controllability(measures, "min_room_size", min_room_size, "floor_fraction")
        record_controllability(measures, "max_room_size", max_room_size, "floor_fraction")
        record_controllability(measures, "map_width", map_width, "floor_fraction")
        record_controllability(measures, "map_height", map_height, "floor_fraction")
        record_controllability(measures, "min_node_size", min_node_size, "floor_fraction")
        record_controllability(measures, "max_node_size", max_node_size, "floor_fraction")

        # registra gli stessi campioni in una struttura globale per aggregare across-runs
        global_sensitivity["min_room_size"].append((min_room_size, measures.features["feature_vector"]["floor_fraction"]))
        global_sensitivity["max_room_size"].append((max_room_size, measures.features["feature_vector"]["floor_fraction"]))
        global_sensitivity["map_width"].append((map_width, measures.features["feature_vector"]["floor_fraction"]))
        global_sensitivity["map_height"].append((map_height, measures.features["feature_vector"]["floor_fraction"]))
        global_sensitivity["min_node_size"].append((min_node_size, measures.features["feature_vector"]["floor_fraction"]))
        global_sensitivity["max_node_size"].append((max_node_size, measures.features["feature_vector"]["floor_fraction"]))

        # ------ BLIND AGENT ------
        dungeon, seed, topo, measures = generate_blind_dungeon(config)
        measures_list.append(measures)
        saveMap(dungeon, "agent_blind_" + str(seed) + ".txt", "blind_agent")
        saveMap(topo, "agent_blind_topo_" + str(seed) + ".txt", "blind_agent")
        measures.to_json(f"Python/results/blind_jsons/blind_{seed}.json")

        # dopo che 'measures' è stato prodotto e post_process_measures è stato eseguito
        # registra campioni per la controllabilità (per run singolo)
        # usa record_controllability per popolare m.sensitivity_data (utile per analisi locali)
        record_controllability(measures, "prob_room", prob_room, "room_count")
        record_controllability(measures, "prob_corridor", prob_corridor, "corridor_count")

        # registra gli stessi campioni in una struttura globale per aggregare across-runs
        global_sensitivity["prob_room"].append((prob_room, measures.features["feature_vector"]["floor_fraction"]))
        global_sensitivity["prob_corridor"].append((prob_corridor, measures.features["feature_vector"]["floor_fraction"]))
        global_sensitivity["map_width"].append((map_width, measures.features["feature_vector"]["floor_fraction"]))
        global_sensitivity["map_height"].append((map_height, measures.features["feature_vector"]["floor_fraction"]))

        # ------ LOOK-AHEAD AGENT ------
        dungeon, seed, topo, measures = generate_lookahead_dungeon(config)
        measures_list.append(measures)
        saveMap(dungeon, "agent_lookahead_" + str(seed) + ".txt", "lookahead_agent")
        saveMap(topo, "agent_lookahead_topo_" + str(seed) + ".txt", "lookahead_agent")
        measures.to_json(f"Python/results/lookahead_jsons/lookahead_{seed}.json")

        # dopo che 'measures' è stato prodotto e post_process_measures è stato eseguito
        # registra campioni per la controllabilità (per run singolo)
        # usa record_controllability per popolare m.sensitivity_data (utile per analisi locali)
        record_controllability(measures, "max_room_size", max_room_size, "floor_fraction")
        record_controllability(measures, "min_room_size", min_room_size, "floor_fraction")
        record_controllability(measures, "map_width", map_width, "floor_fraction")
        record_controllability(measures, "map_height", map_height, "floor_fraction")
        record_controllability(measures, "min_corridor_size", min_corridor_size, "floor_fraction")
        record_controllability(measures, "max_corridor_size", max_corridor_size, "floor_fraction")

        # registra gli stessi campioni in una struttura globale per aggregare across-runs
        global_sensitivity["max_room_size"].append((max_room_size, measures.features["feature_vector"]["floor_fraction"]))
        global_sensitivity["min_room_size"].append((min_room_size, measures.features["feature_vector"]["floor_fraction"]))
        global_sensitivity["map_width"].append((map_width, measures.features["feature_vector"]["floor_fraction"]))
        global_sensitivity["map_height"].append((map_height, measures.features["feature_vector"]["floor_fraction"]))
        global_sensitivity["min_corridor_size"].append((min_corridor_size, measures.features["feature_vector"]["floor_fraction"]))
        global_sensitivity["max_corridor_size"].append((max_corridor_size, measures.features["feature_vector"]["floor_fraction"]))

        # ------ CELLULAR AUTOMATA ------
        dungeon, seed, topo, measures = generate_cellular_dungeon(config)
        measures_list.append(measures)
        saveMap(dungeon, "cellular_automata_" + str(seed) + ".txt", "cellular_automata")
        saveMap(topo, "cellular_automata_topo_" + str(seed) + ".txt", "cellular_automata")
        measures.to_json(f"Python/results/cellular_jsons/cellular_{seed}.json")

        # dopo che 'measures' è stato prodotto e post_process_measures è stato eseguito
        # registra campioni per la controllabilità (per run singolo)
        # usa record_controllability per popolare m.sensitivity_data (utile per analisi locali)
        record_controllability(measures, "initial_chance", initial_chance, "floor_fraction")
        record_controllability(measures, "iterations", iterations, "floor_fraction")
        record_controllability(measures, "map_width", map_width, "floor_fraction")
        record_controllability(measures, "map_height", map_height, "floor_fraction")
        record_controllability(measures, "num_of_walls", num_of_walls, "floor_fraction")

        # registra gli stessi campioni in una struttura globale per aggregare across-runs
        global_sensitivity["initial_chance"].append((initial_chance, measures.features["feature_vector"]["floor_fraction"]))
        global_sensitivity["iterations"].append((iterations, measures.features["feature_vector"]["floor_fraction"]))
        global_sensitivity["map_width"].append((map_width, measures.features["feature_vector"]["floor_fraction"]))
        global_sensitivity["map_height"].append((map_height, measures.features["feature_vector"]["floor_fraction"]))
        global_sensitivity["num_of_walls"].append((num_of_walls, measures.features["feature_vector"]["floor_fraction"]))

        # ------ RANDOM WALK ------
        dungeon, seed, topo, measures = generate_random_walk(config)
        measures_list.append(measures)
        saveMap(dungeon, "random_walk_" + str(seed) + ".txt", "random_walk")
        saveMap(topo, "random_walk_topo_" + str(seed) + ".txt", "random_walk")
        measures.to_json(f"Python/results/random_jsons/random_{seed}.json")

        # dopo che 'measures' è stato prodotto e post_process_measures è stato eseguito
        # registra campioni per la controllabilità (per run singolo)
        # usa record_controllability per popolare m.sensitivity_data (utile per analisi locali)
        record_controllability(measures, "target_floor", target_floor, "floor_fraction")
        record_controllability(measures, "map_width", map_width, "floor_fraction")
        record_controllability(measures, "map_height", map_height, "floor_fraction")

        # registra gli stessi campioni in una struttura globale per aggregare across-runs
        global_sensitivity["target_floor"].append((target_floor, measures.features["feature_vector"]["floor_fraction"]))
        global_sensitivity["map_width"].append((map_width, measures.features["feature_vector"]["floor_fraction"]))
        global_sensitivity["map_height"].append((map_height, measures.features["feature_vector"]["floor_fraction"]))

        # ------ MAZE ------
        dungeon, seed, topo, measures = generate_maze(config)
        measures_list.append(measures)
        saveMap(dungeon, "maze_" + str(seed) + ".txt", "maze_generation")
        saveMap(topo, "maze_topo_" + str(seed) + ".txt", "maze_generation")
        measures.to_json(f"Python/results/maze_jsons/maze_{seed}.json")

        # dopo che 'measures' è stato prodotto e post_process_measures è stato eseguito
        # registra campioni per la controllabilità (per run singolo)
        # usa record_controllability per popolare m.sensitivity_data (utile per analisi locali)
        record_controllability(measures, "maze_width", maze_width, "floor_fraction")
        record_controllability(measures, "maze_height", maze_height, "floor_fraction")

        # registra gli stessi campioni in una struttura globale per aggregare across-runs
        global_sensitivity["maze_width"].append((maze_width, measures.features["feature_vector"]["floor_fraction"]))
        global_sensitivity["maze_height"].append((maze_height, measures.features["feature_vector"]["floor_fraction"]))

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

    # ------ Calcolo sensitivities aggregate su tutti i run ------
    # crea un Measures temporaneo per riutilizzare compute_sensitivity (opzionale)
    agg = Measures(seed = None, label="sensitivity_agg", input_params = config)

    # trasferisci i campioni globali in agg.sensitivity_data
    for pname, samples in global_sensitivity.items():
        # samples è lista di tuple (param_value, feature_value)
        agg.sensitivity_data[pname] = [(float(x), float(y)) for x, y in samples]

        # aggiorna anche control_coverage (come fa record_control_sample)
        vals = [v for v, _ in agg.sensitivity_data[pname]]
        if vals:
            agg.control_coverage[pname] = {"min": min(vals), "max": max(vals), "unique": len(set(vals))}

    # Raggruppa i campioni globali per generator label
    # Assunzione: ogni measures ha un attributo 'label' che contiene il token del generatore (es. 'bsp_', 'blind_')
    per_generator_samples = defaultdict(lambda: defaultdict(list))
    # popola per_generator_samples leggendo measures_list (tutti i run)
    for m in measures_list:
        label = getattr(m, "label", "") or ""
        # estrai il token generatore (es. 'bsp' da 'bsp_measures_123')
        # regola questa estrazione in base al formato esatto delle tue label
        token = label.split("_")[0] if "_" in label else label
        # per ogni parametro che hai raccolto in m.sensitivity_data, sposta i campioni
        for pname, samples in m.sensitivity_data.items():
            # samples sono tuple (param_value, feature_value)
            per_generator_samples[token][pname].extend(samples)

    # crea un agg per ogni generatore e aggiungilo a measures_list se contiene sensitivities
    for token, samples_dict in per_generator_samples.items():
        agg, computed = build_agg_from_samples(token, samples_dict)
        # controlla se agg ha sensitivities calcolate
        sens_keys = [k for k in agg.features.keys() if k.endswith("_sens")]
        if sens_keys:
            measures_list.append(agg)
            print(f"✔ Aggiunto aggregato per {token} con keys: {sens_keys}")
        else:
            print(f"⚠ Nessuna sensitivity calcolata per {token}; aggregato non aggiunto.")

    # calcola la sensitivity per ogni parametro e salva i risultati in agg.features
    # TODO: maybe remove this -> doppia scrittura di sensivity (maze)
    # for pname in list(agg.sensitivity_data.keys()):
        #agg.compute_sensitivity(pname)

    #agg.to_json("Python/results/sensitivity_aggregate.json")

    measures_list.append(agg)

    Measures.save_batch(measures_list)
    diversity = Measures.diversity_stats(measures_list)
    print(diversity)
    # aggragate mescola tutti i tipi di generatori
    # summary = Measures.aggregate(measures_list)
    # print(summary)

    print("\nTutte le mappe sono state generate e salvate nella cartella 'maps/'.")
