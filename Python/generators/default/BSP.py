import random
import copy

from Python.generators.terrain.terrain_CA import terrain_CA_from_dungeon, terrain_to_ascii
from Python.generators.objects.place_objects import place_objects_on_terrain
from Python.generators.topology.classify_cells import classify_cells, topo_to_ascii
from Python.measures.measures import Measures
from Python.measures.postprocess import post_process_measures
from Python.meta import Terrain


# Nodo dell’albero BSP
class Node:

    def __init__(self, x, y, w, h):
        
        self.x, self.y = x, y
        self.w, self.h = w, h
        self.left = None
        self.right = None
        self.room = None
        self.corridors = []

    # ritorna False se il nodo è già diviso o troppo piccolo per essere diviso ulteriormente,
    # altrimenti divide il nodo in due e ritorna True
    def split(self, config):
        
        if self.left or self.right:
            return False

        horizontal_split = random.choice([True, False])

        # nel caso in cui abbia un'area sbilanciata forzo un certo tipo di taglio
        if self.w > self.h and self.w / self.h >= 1.25:
            horizontal_split = False

        elif self.h > self.w and self.h / self.w >= 1.25:
            horizontal_split = True

        # calcola il punto di split in modo che entrambe le parti siano almeno MIN_NODE_SIZE
        max_split = (self.h if horizontal_split else self.w) - config["min_node_size"]
        if max_split <= config["min_node_size"]:
            return False

        split = random.randint(config["min_node_size"], max_split) # TODO: max split potrebbe essere un altro parametro

        # definisci due nuovi nodi figli in base al punto di split e alla direzione di split
        if horizontal_split:
            self.left = Node(self.x, self.y, self.w, split)
            self.right = Node(self.x, self.y + split, self.w, self.h - split)

        else:
            self.left = Node(self.x, self.y, split, self.h)
            self.right = Node(self.x + split, self.y, self.w - split, self.h)

        return True

    def create_rooms(self, config):
        if self.left or self.right:
            if self.left:
                self.left.create_rooms(config)

            if self.right:
                self.right.create_rooms(config)

            # Corridoio tra stanze/figli
            if self.left and self.right:
                room1 = self.left.get_room()
                room2 = self.right.get_room()

                if room1 and room2:
                    self.create_corridor(room1, room2)

        else:
            # Crea stanza relativa al nodo
            # room_x e room_y sono le coordinate del punto in alto a sinistra della stanza
            # TODO: se le stanze si rompono qui potrebbe esserci un problema
            min_size = config["min_room_size"]

            max_w = min(self.w - 2, config["max_room_size"])
            max_h = min(self.h - 2, config["max_room_size"])

            if max_w < min_size or max_h < min_size:
                self.room = None
                return

            room_w = random.randint(min_size, max_w)
            room_h = random.randint(min_size, max_h)

            room_x = random.randint(self.x + 1, self.x + self.w - room_w - 1)
            room_y = random.randint(self.y + 1, self.y + self.h - room_h - 1)

            self.room = (room_x, room_y, room_w, room_h)

    def get_room(self):

        if self.room:
            return self.room

        else:
            rooms = []

            if self.left:
                r = self.left.get_room()

                if r:
                    rooms.append(r)

            if self.right:
                r = self.right.get_room()

                if r:
                    rooms.append(r)

            # se ci sono più stanze nei figli, ne scelgo una a caso da restituire
            return random.choice(rooms) if rooms else None

    def create_corridor(self, room1, room2):
        # Scegli un punto casuale in ciascuna stanza sia per x che per y
        # room[0] = x, room[1] = y, room[2] = width, room[3] = height
        x1 = random.randint(room1[0], room1[0] + room1[2] - 1)
        y1 = random.randint(room1[1], room1[1] + room1[3] - 1)
        x2 = random.randint(room2[0], room2[0] + room2[2] - 1)
        y2 = random.randint(room2[1], room2[1] + room2[3] - 1)

        # se random.choice([True, False]) è True, crea un corridoio orizzontale da (x1, y1) a (x2, y1)
        # e poi uno verticale da (x2, y1) a (x2, y2)
        # altrimenti, crea un corridoio verticale da (x1, y1) a (x1, y2) e poi uno orizzontale da (x1, y2) a (x2, y2)
        if random.choice([True, False]):
            self.corridors.append(((x1, y1), (x2, y1)))
            self.corridors.append(((x2, y1), (x2, y2)))

        else:
            self.corridors.append(((x1, y1), (x1, y2)))
            self.corridors.append(((x1, y2), (x2, y2)))

# Utility
def collect_all_nodes(node, out):
    out.append(node)

    if node.left:
        collect_all_nodes(node.left, out)

    if node.right:
        collect_all_nodes(node.right, out)

def collect_rooms(node, out):
    if node.room:
        out.append(node.room)

    if node.left:
        collect_rooms(node.left, out)

    if node.right:
        collect_rooms(node.right, out)


# Funzione principale per generare il dungeon BSP
def generate_bsp_dungeon(config, dungeon = None, seed = None):
    if seed is None:
        seed = random.randint(0, 2 ** 32 - 1)

    random.seed(seed)

    m = Measures (seed = seed, label = "bsp_measures_" + str(seed), input_params = copy.deepcopy(config))
    m.start_wall()

    root = Node(0, 0, config["map_width"], config["map_height"])
    nodes = [root]

    if not dungeon:
        dungeon = [[Terrain.WALL for _ in range(config["map_width"])] for _ in range(config["map_height"])]

    # Divisione ricorsiva
    did_split = True

    while did_split:
        did_split = False
        new_nodes = []

        for node in nodes:
            if node.w > config["max_node_size"] or node.h > config["max_node_size"]: # or random.random() > 0.8:
                if node.split(config):
                    new_nodes.append(node.left)
                    new_nodes.append(node.right)
                    did_split = True

                else:
                    new_nodes.append(node)

            else:
                new_nodes.append(node)

        nodes = new_nodes

    with m.time_phase("dungeon_generation"):
        # Creazione stanze e corridoi una volta che l'albero è stato costruito
        root.create_rooms(config)

        # Disegna stanze
        for node in nodes:
            if node.room:
                room_x, room_y, room_w, room_h = node.room
                for i in range(room_x, room_x + room_w):
                    for j in range(room_y, room_y + room_h):
                        dungeon[j][i] = Terrain.FLOOR

        # Disegna corridoi
        def draw_corridor(p1, p2):
            x1, y1 = p1
            x2, y2 = p2
            if x1 == x2:
                for y in range(min(y1, y2), max(y1, y2) + 1):
                    dungeon[y][x1] = Terrain.FLOOR
            elif y1 == y2:
                for x in range(min(x1, x2), max(x1, x2) + 1):
                    dungeon[y1][x] = Terrain.FLOOR

        # Disegna corridoi per TUTTI i nodi
        all_nodes = []
        collect_all_nodes(root, all_nodes)

        for node in all_nodes:
            for c in node.corridors:
                draw_corridor(*c)

    # ritorna la lista di tutte le stanze (x, y, w, h) per eventuali usi futuri
    rooms = []
    collect_rooms(root, rooms)

    with m.time_phase("classify_cells"):
        topo, components, rooms = classify_cells(dungeon, config)
    with m.time_phase("terrain_generation"):
        terrain = terrain_CA_from_dungeon(dungeon, topo, components, config, seed = seed)
    with m.time_phase("objects_generation"):
        objects = place_objects_on_terrain(terrain, topo, config)
    ascii_map = terrain_to_ascii(dungeon, terrain, objects, config)
    ascii_topo = topo_to_ascii(topo, config)

    m.end_wall()

    m.set_meta("dungeon", dungeon)
    m.set_meta("topo", topo)
    m.set_meta("components", components)
    m.set_meta("terrain", terrain)
    m.set_meta("objects", objects)
    m.set_meta("rooms", rooms)

    post_process_measures(m, config)

    return ascii_map, rooms, seed, ascii_topo, m