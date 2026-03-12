from collections import deque
from Python.meta import MIN_ROOM_SIZE, MAX_ROOM_SIZE, MIN_CORRIDOR_SIZE, MAX_CORRIDOR_SIZE, MAP_HEIGHT, MAP_WIDTH

import copy


# Classe CSP e funzioni per fare un modello dei problemi:

class CSP:

    def __init__(self, variables, domains, constraints):

        self.variables = variables
        self.domains = domains
        self.constraints = constraints

    def isConsistent(self, var, value, assignment):

        for (neighbor, constraint) in self.constraints.get(var, []):

            if neighbor in assignment:

                if not constraint(value, assignment[neighbor]):
                    return False

        return True

    def isComplete(self, assignment):
        # controllo se variables è un sottoinsieme di assignment.keys()
        return set(self.variables) <= set(assignment.keys())


def getDungeonAsCsp():

    variables = []
    domains = {}
    constraints = {}

    # Creazione di variabili e domini: tutte le possibili stanze e corridoi
    for w in range(MIN_ROOM_SIZE, MAX_ROOM_SIZE):
        for h in range(MIN_ROOM_SIZE, MAX_ROOM_SIZE):
            for x in range(MAP_WIDTH):
                for y in range(MAP_HEIGHT):
                    var = (x, y, w, h)
                    variables.append(var)
                    # dominio di una variabile/room:
                    # x e y sono già fissati (compresi tra 0 e MAP_WIDTH/MAP_HEIGHT)
                    # w e h possono essere limitati da stanze o corridoi vicini
                    domains[var] = [(w, h) for w in range(MIN_ROOM_SIZE, MAX_ROOM_SIZE) for h in range(MIN_ROOM_SIZE, MAX_ROOM_SIZE)]

    # Vincolo "different cell value": due celle che non possono avere lo stesso valore
    def diffCellValueConstraint(x, y):
        return x != y

    # Definizione dei vincoli per ogni cella: stessa riga, colonna e blocco 3x3
    for var in variables:

        r, c = var
        neighbors = set()  # Uso un set per raccogliere le celle in conflitto con quella corrente

        # Stessa riga e colonna
        for i in range(9):

            if i != c: neighbors.add((r, i))
            if i != r: neighbors.add((i, c))

        # Stesso blocco 3x3
        br, bc = 3 * (r // 3), 3 * (c // 3)  # Divisione intera

        for i in range(br, br + 3):

            for j in range(bc, bc + 3):

                if (i, j) != var:
                    neighbors.add((i, j))

        # constraints è un dizionario che associa ad una variabile una lista di
        # neighbors e il vincolo che ha con ciascuno di essi
        constraints[var] = [(n, diffCellValueConstraint) for n in neighbors]

    return CSP(variables, domains, constraints)


def mapColoringToCsp(map_data, colors=["red", "green", "blue"]):

    variables = list(map_data.keys())
    domains = {var: colors[:] for var in variables}
    constraints = {}

    # Vincolo: due regioni adiacenti devono avere colori diversi
    def diffColorConstraint(x, y):
        return x != y

    for var in variables:

        neighbors = map_data[var]
        constraints[var] = [(n, diffColorConstraint) for n in neighbors]

    return CSP(variables, domains, constraints)


# Funzioni per il solver:

def revise(csp, xi, xj):

    # Esegue il cross-out sul dominio di della i-esima variabile xi
    # per garantire arc-consistency tra xi e la j-esima variabile xj.
    # Restituisce True se il dominio di xi viene ridotto.

    revised = False
    to_remove = []

    # Per ogni valore del dominio x in xi, verifico se esiste almeno un valore in xj che soddisfa il vincolo,
    # altrimenti lo rimuovo.
    for x in csp.domains[xi]:

        satisfies = False

        # Ciclo tra i vincoli associati a xi per trovare quello relativo a xj.
        for (neighbor, constraint) in csp.constraints.get(xi, []):

            if neighbor == xj:

                for y in csp.domains[xj]:

                    if constraint(x, y):

                        satisfies = True
                        break

                # Esco dal ciclo sui vincoli se ho trovato quello per xj.
                break

        if not satisfies:
            to_remove.append(x)

    # Rimuovo i valori non consistenti dal dominio di xi.
    for x in to_remove:

        csp.domains[xi].remove(x)
        revised = True

    return revised


def ac3(csp):

    # Restituisce True se tutti gli archi risultano consistent,
    # altrimenti False se un dominio diventa vuoto.

    print("-Propagazione dell'inferenza...")

    queue = deque()
    # Uso una coda per avere un accesso FIFO
    # al fine di avere un'inferenza sui vincoli aggiunti per primi.

    # Inizializza la coda con ogni arco (xi, xj) derivante dai vincoli.
    for xi in csp.variables:

        for (xj, _) in csp.constraints.get(xi, []):
            queue.append((xi, xj)) # questa coppia rappresenta un arco nel grafo dei vincoli

    while queue:

        xi, xj = queue.popleft()

        # Inferenza:
        if revise(csp, xi, xj):

            if not csp.domains[xi]:
                return False  # Fallimento: il dominio di xi è stato svuotato

            # aggiungo a queue ogni arco (xk, xi) dove xk è un vicino di xi diverso da xj,
            # tali archi verranno ricontrollati per la consistency
            # (che potrebbe essersi modificata a seguito del revise).
            for (xk, _) in csp.constraints.get(xi, []):

                if xk != xj: # evito di reinserire l'arco (xi, xj)
                    queue.append((xk, xi))

    return True


def dfsCycle(graph, node, visited, parent, path):

    # DFS che restituisce il path di un ciclo (nodi del ciclo) al fine di trovare un cycle-cutset.

    visited.add(node)
    path.append(node)

    for neighbor in graph.get(node, []):

        if neighbor not in visited:
            cycle = dfsCycle(graph, neighbor, visited, node, path)

            if cycle:
                return cycle

        elif neighbor != parent and neighbor in path:

            cycle_start = path.index(neighbor) # identifico da dove inizia il ciclo
            return path[cycle_start:]

    path.pop() # backtracking
    # (il nodo attuale non farà più parte dell'attuale esplorazione la quale continua con la chiamata precedente)
    return None


def findCycleCutset(graph):

    visited = set()

    for node in graph:

        if node not in visited:

            cycle = dfsCycle(graph, node, visited, None, [])

            if cycle:

                print("-Ciclo individuato!")
                return cycle

    return None  # Se non ci sono cicli


def treeSolver(csp, assignment):

    if csp.isComplete(assignment):
        return assignment

    unassigned = [v for v in csp.variables if v not in assignment]

    if not unassigned:
        return None

    # MRV
    domains_dict = {var: len(csp.domains[var]) for var in unassigned}
    var = min(domains_dict, key=domains_dict.get)

    for value in csp.domains[var]:

        if csp.isConsistent(var, value, assignment):

            assignment[var] = value
            result = treeSolver(csp, assignment)

            if result is not None:
                return result

            del assignment[var]

    return None


def buildConstraintGraph(csp, assignment):

    graph = {var: [] for var in assignment}  # dizionario

    for var in assignment:

        for (neighbor, _) in csp.constraints.get(var, []):

            if neighbor in assignment:
                graph[var].append(neighbor)

    return graph


def backtrackingSearch(csp, assignment={}):

    # Esegue la ricerca ricorsiva con backtracking e inferenza AC-3.
    # Se giunge ad un cutset aciclico chiama treeSolver per risolvere il problema.

    if csp.isComplete(assignment):
        return assignment

    unassigned = [var for var in csp.variables if var not in assignment]

    if not unassigned:
        return assignment

    # Seleziona la variabile con l'euristica Minimum Remaining Values (MRV)
    domains_dict = {var: len(csp.domains[var]) for var in unassigned}
    var = min(domains_dict, key = domains_dict.get)

    for value in csp.domains[var]:

        if csp.isConsistent(var, value, assignment):

            # Creo un sotto-problema locale (cutset) per non perdere progresso fatto fino alla
            # chiamata attuale del backtrackingSearch nel caso in cui non si trovi una soluzione.
            # (è più facile da scrivere ma meno efficiente in termini di memoria)

            # Copia dell'assegnamento corrente e aggiungo (var, value)
            local_assignment = assignment.copy()
            local_assignment[var] = value

            # Copia profonda del CSP per non modificare l'originale.
            local_csp = copy.deepcopy(csp)

            # Fisso il valore assegnato riducendo il dominio a value.
            local_csp.domains[var] = [value]

            # Applica AC-3 per propagare l'inferenza
            if ac3(local_csp):

                graph = buildConstraintGraph(local_csp,local_assignment)

                # Trova se ci sono cicli nel grafo dei vincoli ed eventualmente trova un cycle-cutset
                cycle_cutset = findCycleCutset(graph)

                if cycle_cutset is not None:

                    # Rimozione delle variabili del cycle-cutset dai domini
                    # tali variabili del cycle-cutset saranno così fissate e non
                    # interferiscono con il loro ciclo nel resto del problema
                    for var in cycle_cutset:

                        # aggiungo un if per non modificare le variabili già fissate
                        if var not in local_assignment:
                            local_csp.domains.pop(var, None)

                    # Dopo aver rimosso le variabili del cycle-cutset, si può risolvere come albero
                    print("-Applicazione del tree solver...")
                    result = treeSolver(local_csp, local_assignment)

                    if result is not None:
                        return result

                # Altrimenti, prosegui con il backtracking
                else:

                    print("-Continuo con il backtracking...")
                    result = backtrackingSearch(local_csp, local_assignment)

                    if result is not None:
                        return result

    return None


# Funzioni per la stampa e controllo dei risultati

def printSudokuSolution(assignment):

    if assignment is None:

        print("Nessuna soluzione trovata per questo Sudoku.")
        print()
        return

    grid = [[0 for _ in range(9)] for _ in range(9)]

    for (row, col), value in assignment.items():
        grid[row][col] = value

    for i in range(9):

        if i % 3 == 0 and i != 0:
            print("-" * 21)

        for j in range(9):

            if j % 3 == 0 and j != 0 and j != 9:
                print("|", end=" ")

            print(grid[i][j], end=" ")

        print()

    print()


def printMapSolution(assignment):

    if assignment is None:

        print("Nessuna soluzione trovata per la mappa.")
        print()
        return

    for region in assignment.keys():
        print(region, ":", assignment[region])

    print()