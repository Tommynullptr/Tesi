import random

from Python.generators.terrain.terrain_CA import terrainCAFromDungeon, terrainToAscii
from Python.generators.objects.place_objects import placeObjectsOnTerrain
from Python.generators.topology.classify_cells import classifyCells, topoToAscii
from Python.meta import MAP_WIDTH, MAP_HEIGHT, MIN_NODE_SIZE, MAX_NODE_SIZE, Terrain


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
    def split(self):
        
        if self.left or self.right:
            return False

        horizontal_split = random.choice([True, False])

        # nel caso in cui abbia un'area sbilanciata forzo un certo tipo di taglio
        if self.w > self.h and self.w / self.h >= 1.25:
            horizontal_split = False

        elif self.h > self.w and self.h / self.w >= 1.25:
            horizontal_split = True

        # calcola il punto di split in modo che entrambe le parti siano almeno MIN_NODE_SIZE
        max_split = (self.h if horizontal_split else self.w) - MIN_NODE_SIZE
        if max_split <= MIN_NODE_SIZE:
            return False

        split = random.randint(MIN_NODE_SIZE, max_split)

        # definisci due nuovi nodi figli in base al punto di split e alla direzione di split
        if horizontal_split:
            self.left = Node(self.x, self.y, self.w, split)
            self.right = Node(self.x, self.y + split, self.w, self.h - split)

        else:
            self.left = Node(self.x, self.y, split, self.h)
            self.right = Node(self.x + split, self.y, self.w - split, self.h)

        return True

    def createRooms(self):
        if self.left or self.right:
            if self.left:
                self.left.createRooms()

            if self.right:
                self.right.createRooms()

            # Corridoio tra stanze/figli
            if self.left and self.right:
                room1 = self.left.getRoom()
                room2 = self.right.getRoom()

                if room1 and room2:
                    self.createCorridor(room1, room2)

        else:
            # Crea stanza relativa al nodo
            # room_x e room_y sono le coordinate del punto in alto a sinistra della stanza
            room_w = random.randint(5, self.w - 2)
            room_h = random.randint(5, self.h - 2)
            room_x = random.randint(self.x + 1, self.x + self.w - room_w - 1)
            room_y = random.randint(self.y + 1, self.y + self.h - room_h - 1)

            self.room = (room_x, room_y, room_w, room_h)

    def getRoom(self):

        if self.room:
            return self.room

        else:
            rooms = []

            if self.left:
                r = self.left.getRoom()

                if r:
                    rooms.append(r)

            if self.right:
                r = self.right.getRoom()

                if r:
                    rooms.append(r)

            # se ci sono più stanze nei figli, ne scelgo una a caso da restituire
            return random.choice(rooms) if rooms else None

    def createCorridor(self, room1, room2):
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
def collectAllNodes(node, out):
    out.append(node)

    if node.left:
        collectAllNodes(node.left, out)

    if node.right:
        collectAllNodes(node.right, out)

def collectRooms(node, out):
    if node.room:
        out.append(node.room)

    if node.left:
        collectRooms(node.left, out)

    if node.right:
        collectRooms(node.right, out)


# Funzione principale per generare il dungeon BSP
def generateBspDungeon(dungeon = None, seed = None):
    if seed is None:
        seed = random.randint(0, 2 ** 32 - 1)

    random.seed(seed)

    root = Node(0, 0, MAP_WIDTH, MAP_HEIGHT)
    nodes = [root]

    if not dungeon:
        dungeon = [[Terrain.WALL for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]

    # Divisione ricorsiva
    did_split = True

    while did_split:
        did_split = False
        new_nodes = []

        for node in nodes:
            if node.w > MAX_NODE_SIZE or node.h > MAX_NODE_SIZE or random.random() > 0.8:
                if node.split():
                    new_nodes.append(node.left)
                    new_nodes.append(node.right)
                    did_split = True

                else:
                    new_nodes.append(node)

            else:
                new_nodes.append(node)

        nodes = new_nodes

    # Creazione stanze e corridoi una volta che l'albero è stato costruito
    root.createRooms()

    # Disegna stanze
    for node in nodes:
        if node.room:
            room_x, room_y, room_w, room_h = node.room
            for i in range(room_x, room_x + room_w):
                for j in range(room_y, room_y + room_h):
                    dungeon[j][i] = Terrain.FLOOR

    # Disegna corridoi
    def drawCorridor(p1, p2):
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
    collectAllNodes(root, all_nodes)

    for node in all_nodes:
        for c in node.corridors:
            drawCorridor(*c)

    # ritorna la lista di tutte le stanze (x, y, w, h) per eventuali usi futuri
    rooms = []
    collectRooms(root, rooms)

    topo, components = classifyCells(dungeon)
    terrain = terrainCAFromDungeon(dungeon, topo, components, seed = seed)
    objects = placeObjectsOnTerrain(terrain, topo)
    ascii_map = terrainToAscii(dungeon, terrain, objects)
    ascii_topo = topoToAscii(topo)

    return ascii_map, rooms, seed, ascii_topo