import sys
import math

"""
Niveau 1 – Selenia City
-----------------------

Objectif de cette version :
- Avoir un code PROPRE, LISIBLE et BIEN COMMENTÉ.
- Utiliser une stratégie simple mais déjà "intelligente" :
  - Construire des tubes magnétiques en évitant :
      * les croisements avec d'autres tubes,
      * le passage au travers d'un bâtiment,
      * plus de 5 tubes par bâtiment.
  - Utiliser une approche gloutonne (greedy) :
      * chaque nouveau bâtiment est relié au bâtiment existant le plus proche
        compatible avec les contraintes géométriques.
  - Créer quelques PODs qui font des allers-retours entre 0 et des bâtiments
    connectés pour transporter des astronautes.

Contraintes pratiques :
- On ne connaît pas exactement le format de `building_properties`.
  On suppose qu'il contient au moins :
    * un identifiant de bâtiment (premier entier de la ligne),
    * des coordonnées (deux derniers entiers de la ligne : x y).
  Cette hypothèse fonctionne sur beaucoup de jeux CodinGame.
"""

# ====================================================================================
# 1. Structures de données PERSISTANTES (en dehors de la boucle de jeu)
# ====================================================================================

# Position de chaque bâtiment : building_id -> (x, y)
building_positions: dict[int, tuple[int, int]] = {}

# Type de chaque bâtiment : "landing" (aire d'atterrissage) ou "module"
building_type: dict[int, str] = {}

# Pour les modules : moduleType[building_id] = type du module (1..20)
module_type: dict[int, int] = {}

# Pour les aires d'atterrissage : liste des types d'astronautes qui arrivent chaque mois
landing_astronaut_types: dict[int, list[int]] = {}

# On enregistre tous les bâtiments apparus (pour itérer dessus facilement)
all_buildings: set[int] = set()


# ====================================================================================
# 2. Fonctions utilitaires – géométrie
# ====================================================================================

def orientation(ax: float, ay: float, bx: float, by: float, cx: float, cy: float) -> int:
    """
    Orientation (a -> b -> c)
    > 0 : tournant anti‑horaire
    < 0 : tournant horaire
    = 0 : points alignés
    """
    value = (bx - ax) * (cy - ay) - (by - ay) * (cx - ax)
    if value > 0:
        return 1
    if value < 0:
        return -1
    return 0


def point_on_segment(px: float, py: float, ax: float, ay: float, bx: float, by: float) -> bool:
    """
    Vrai si le point P est sur le segment [A,B] (bords inclus).
    On teste d'abord l'alignement (orientation = 0),
    puis si P est dans le rectangle englobant A et B.
    """
    if orientation(ax, ay, bx, by, px, py) != 0:
        return False

    return (
        min(ax, bx) <= px <= max(ax, bx)
        and min(ay, by) <= py <= max(ay, by)
    )


def segments_intersect(a, b, c, d) -> bool:
    """
    Test classique d'intersection entre deux segments [A,B] et [C,D].
    Ici, on considère toute intersection comme interdite, sauf lorsque
    les segments ne font que se toucher au niveau d'un même point terminal
    (ce cas sera géré AVANT l'appel à cette fonction).
    """
    ax, ay = a
    bx, by = b
    cx, cy = c
    dx, dy = d

    o1 = orientation(ax, ay, bx, by, cx, cy)
    o2 = orientation(ax, ay, bx, by, dx, dy)
    o3 = orientation(cx, cy, dx, dy, ax, ay)
    o4 = orientation(cx, cy, dx, dy, bx, by)

    # Cas général : les segments se croisent strictement.
    if o1 != 0 and o2 != 0 and o3 != 0 and o4 != 0:
        if (o1 != o2) and (o3 != o4):
            return True

    # Cas particuliers : un point est aligné + sur le segment opposé.
    if o1 == 0 and point_on_segment(cx, cy, ax, ay, bx, by):
        return True
    if o2 == 0 and point_on_segment(dx, dy, ax, ay, bx, by):
        return True
    if o3 == 0 and point_on_segment(ax, ay, cx, cy, dx, dy):
        return True
    if o4 == 0 and point_on_segment(bx, by, cx, cy, dx, dy):
        return True

    return False


def tube_is_geometrically_valid(u: int, v: int, existing_tubes: list[tuple[int, int]],
                                max_degree: int, degree: dict[int, int]) -> bool:
    """
    Vérifie qu'un tube (u,v) respecte toutes les contraintes géométriques :
    - Les deux bâtiments ont une position connue
    - Chacun des bâtiments n'a pas déjà 5 tubes
    - Le segment [u,v] ne coupe aucun autre tube existant (hors partage d'extrémité)
    - Le segment [u,v] ne traverse aucun bâtiment (autre que u ou v)
    """
    # Positions connues ?
    if u not in building_positions or v not in building_positions:
        return False

    pu = building_positions[u]
    pv = building_positions[v]

    # Degré max 5 par bâtiment
    if degree.get(u, 0) >= max_degree or degree.get(v, 0) >= max_degree:
        return False

    # 1) Pas de croisement avec un tube existant
    for a, b in existing_tubes:
        # Partage d'extrémité autorisé (on laisse un "noeud" commun)
        if a in (u, v) or b in (u, v):
            continue
        pa = building_positions.get(a)
        pb = building_positions.get(b)
        if pa is None or pb is None:
            continue
        if segments_intersect(pu, pv, pa, pb):
            return False

    # 2) Ne traverse aucun autre bâtiment
    for w in all_buildings:
        if w in (u, v):
            continue
        pw = building_positions.get(w)
        if pw is None:
            continue
        if point_on_segment(pw[0], pw[1], pu[0], pu[1], pv[0], pv[1]):
            return False

    return True


# ====================================================================================
# 2.b Heuristiques de connexion – choix du voisin "intéressant"
# ====================================================================================

def tube_construction_cost(u: int, v: int) -> int:
    """
    Coût estimé de construction d'un tube entre u et v.
    Règle : 1 ressource par 0.1 km de tube, arrondi à l'entier inférieur.
    On considère que les coordonnées sont en km.
    distance = sqrt((dx)^2 + (dy)^2)
    cost = floor(distance / 0.1) = floor(distance * 10)
    """
    if u not in building_positions or v not in building_positions:
        return 10**9  # Très cher => on évitera
    x1, y1 = building_positions[u]
    x2, y2 = building_positions[v]
    dist = math.hypot(x2 - x1, y2 - y1)
    return int(dist * 10)


def find_best_neighbor_for_building(
    b: int,
    remaining_resources: int,
    degree: dict[int, int],
    existing_tubes: list[tuple[int, int]],
) -> tuple[int | None, int]:
    """
    Choisit le "meilleur" bâtiment à relier à b ce tour, en respectant :
      - les contraintes géométriques,
      - la limite de 5 tubes par bâtiment,
      - le budget restant.

    Heuristique :
      - Si b est une aire d'atterrissage :
            essayer d'abord les modules dont le type est présent
            parmi les astronautes de cette aire.
      - Si b est un module :
            essayer d'abord les aires d'atterrissage qui attendent ce type.
      - Sinon / fallback : tester tous les bâtiments, en prenant le plus proche.
    """
    if b not in building_positions:
        return (None, 0)

    # Petite fonction interne pour tester une liste de candidats
    def best_over_candidates(candidates: list[int]) -> tuple[int | None, int]:
        best_neighbor = None
        best_cost = 0
        best_dist2 = None

        bx, by = building_positions[b]

        for other in candidates:
            if other == b:
                continue
            if other not in building_positions:
                continue

            # Limite de degré déjà atteinte pour l'autre extrémité ?
            if degree.get(other, 0) >= MAX_TUBES_PER_BUILDING:
                continue

            # Tube géométriquement valide ?
            if not tube_is_geometrically_valid(
                b,
                other,
                existing_tubes,
                MAX_TUBES_PER_BUILDING,
                degree,
            ):
                continue

            # Coût de construction
            cost = tube_construction_cost(b, other)
            if cost > remaining_resources:
                continue

            # Distance euclidienne (pour favoriser les tubes courts)
            ox, oy = building_positions[other]
            dx = ox - bx
            dy = oy - by
            dist2 = dx * dx + dy * dy

            if best_neighbor is None or dist2 < best_dist2:
                best_neighbor = other
                best_cost = cost
                best_dist2 = dist2

        return best_neighbor, best_cost

    # Liste de tous les bâtiments éligibles connus
    all_candidates = [x for x in all_buildings if x != b and x in building_positions]

    # 1) Priorité basée sur le type de bâtiment
    b_type = building_type.get(b)

    # Candidats "prioritaires" (même type d'usage)
    preferred: list[int] = []

    if b_type == "landing":
        # On cherche d'abord des modules dont le type est compatible
        wanted_types = landing_astronaut_types.get(b, [])
        for other in all_candidates:
            if building_type.get(other) == "module":
                if module_type.get(other) in wanted_types:
                    preferred.append(other)

    elif b_type == "module":
        # On cherche d'abord les aires d'atterrissage qui demandent ce type
        mtype = module_type.get(b)
        for landing_id, types in landing_astronaut_types.items():
            if landing_id == b:
                continue
            if mtype in types and landing_id in building_positions:
                preferred.append(landing_id)

    # 2) On tente d'abord sur les candidats "préférés"
    if preferred:
        neighbor, cost = best_over_candidates(preferred)
        if neighbor is not None:
            return neighbor, cost

    # 3) Sinon, fallback : tous les bâtiments connus
    neighbor, cost = best_over_candidates(all_candidates)
    return neighbor, cost


# ====================================================================================
# 3. Boucle de jeu principale
# ====================================================================================

MAX_TUBES_PER_BUILDING = 5          # Règle du jeu

# On autorise un peu plus de tubes par tour pour mieux connecter la carte,
# tout en restant raisonnable pour ne pas épuiser les ressources trop vite.
MAX_NEW_TUBES_PER_TURN = 6
MAX_NEW_PODS_PER_TURN = 2           # On pourra étendre si les ressources le permettent

while True:
    # --------------------------------------------------------------------------
    # 3.1. Lecture des entrées du tour
    # --------------------------------------------------------------------------
    resources = int(input())  # Ressources disponibles ce tour (on ne les simule pas précisément)

    # ----- Tubes existants ----------------------------------------------------
    num_travel_routes = int(input())
    routes: list[tuple[int, int, int]] = []
    existing_tubes: list[tuple[int, int]] = []  # seulement (u,v) pour la géométrie
    degree: dict[int, int] = {}                # degré de chaque bâtiment (nb de tubes)

    for _ in range(num_travel_routes):
        b1, b2, capacity = [int(j) for j in input().split()]
        routes.append((b1, b2, capacity))
        existing_tubes.append((b1, b2))

        all_buildings.add(b1)
        all_buildings.add(b2)
        degree[b1] = degree.get(b1, 0) + 1
        degree[b2] = degree.get(b2, 0) + 1

    # ----- PODs existants -----------------------------------------------------
    num_pods = int(input())
    pods_serving: set[int] = set()     # bâtiments déjà desservis par au moins un POD
    existing_pod_ids: set[int] = set()

    for _ in range(num_pods):
        parts = input().split()
        if len(parts) < 2:
            continue
        # ID du POD (premier entier)
        try:
            pod_id = int(parts[0])
            existing_pod_ids.add(pod_id)
        except ValueError:
            pod_id = None

        # Deuxième entier = numStops (qu'on peut ignorer pour notre logique)
        # Les bâtiments de l'itinéraire commencent à l'indice 2.
        for token in parts[2:]:
            try:
                bid = int(token)
                if bid != 0:  # on ignore les éventuels 0 dans les itinéraires
                    pods_serving.add(bid)
            except ValueError:
                pass

    # Choisir le prochain ID de POD disponible
    pod_id_counter = 0
    while pod_id_counter in existing_pod_ids:
        pod_id_counter += 1

    # ----- Nouveaux bâtiments (de ce mois) -----------------------------------
    num_new_buildings = int(input())
    new_buildings: list[int] = []

    for _ in range(num_new_buildings):
        parts = input().split()
        # On extrait tous les entiers pour interpréter la ligne
        ints: list[int] = []
        for t in parts:
            try:
                ints.append(int(t))
            except ValueError:
                pass

        if not ints:
            continue

        # Format rappelé :
        #  - Aire d'atterrissage :
        #       0 buildingId coordX coordY numAstronauts astronautType1 ...
        #  - Module :
        #       moduleType buildingId coordX coordY
        first = ints[0]
        if first == 0 and len(ints) >= 5:
            # Aire d'atterrissage
            building_id = ints[1]
            x = ints[2]
            y = ints[3]
            num_astronauts = ints[4]
            astro_types = ints[5:5 + num_astronauts]

            building_positions[building_id] = (x, y)
            building_type[building_id] = "landing"
            landing_astronaut_types[building_id] = astro_types

        elif first > 0 and len(ints) >= 4:
            # Module lunaire
            mtype = ints[0]
            building_id = ints[1]
            x = ints[2]
            y = ints[3]

            building_positions[building_id] = (x, y)
            building_type[building_id] = "module"
            module_type[building_id] = mtype
        else:
            # Ligne inattendue, on l'ignore
            continue

        new_buildings.append(building_id)
        all_buildings.add(building_id)

    # --------------------------------------------------------------------------
    # 3.2. Construction des actions
    # --------------------------------------------------------------------------
    actions: list[str] = []

    # === 3.2.1. Tubes : relier les nouveaux bâtiments au réseau ==============
    # Stratégie gloutonne "typée" :
    #   - Pour chaque nouveau bâtiment, essayer de le relier à un bâtiment
    #     "compatible" (landing <-> module du bon type) quand c'est possible.
    #   - Sinon, relier au bâtiment existant le plus proche.
    #   - Toujours respecter :
    #       * contraintes géométriques,
    #       * limite de 5 tubes par bâtiment,
    #       * budget disponible de ressources.

    new_tubes_this_turn = 0
    remaining_resources = resources

    for b in new_buildings:
        if new_tubes_this_turn >= MAX_NEW_TUBES_PER_TURN:
            break
        if remaining_resources <= 0:
            break

        if b not in building_positions:
            # On n'a pas de coordonnées fiables, mieux vaut ne rien faire
            continue

        neighbor, cost = find_best_neighbor_for_building(
            b,
            remaining_resources,
            degree,
            existing_tubes,
        )

        if neighbor is not None and cost <= remaining_resources:
            # On ajoute le tube b <-> neighbor
            actions.append(f"TUBE {b} {neighbor}")
            existing_tubes.append((b, neighbor))
            degree[b] = degree.get(b, 0) + 1
            degree[neighbor] = degree.get(neighbor, 0) + 1
            new_tubes_this_turn += 1
            remaining_resources -= cost

    # === 3.2.2. PODs : desservir les aires d'atterrissage ====================
    # On suit le conseil de l'énoncé : des allers‑retours simples sur une ligne.
    # On crée des PODs sur les tubes (existants) reliant directement
    # une aire d'atterrissage à un autre bâtiment (souvent un module).

    candidate_pod_pairs: list[tuple[int, int]] = []  # (landing, other)
    for b1, b2, _cap in routes:
        # Cas 1 : b1 est une aire d'atterrissage, b2 un autre bâtiment
        if building_type.get(b1) == "landing" and b2 not in pods_serving:
            candidate_pod_pairs.append((b1, b2))
        # Cas 2 : b2 est une aire d'atterrissage, b1 un autre bâtiment
        if building_type.get(b2) == "landing" and b1 not in pods_serving:
            candidate_pod_pairs.append((b2, b1))

    # Coût fixe d'un POD : 1000 ressources
    POD_COST = 1000

    # On crée au plus quelques PODs par tour, si on a suffisamment de ressources
    pods_created = 0
    for landing_id, target in candidate_pod_pairs:
        if pods_created >= MAX_NEW_PODS_PER_TURN:
            break

        if remaining_resources < POD_COST:
            break

        # Route simple : landing -> target -> landing -> target ...
        route_str = f"{landing_id} {target} {landing_id} {target} {landing_id} {target} {landing_id} {target}"
        actions.append(f"POD {pod_id_counter} {route_str}")
        pod_id_counter += 1
        pods_created += 1
        pods_serving.add(target)
        remaining_resources -= POD_COST

    # --------------------------------------------------------------------------
    # 3.3. Sortie des actions
    # --------------------------------------------------------------------------
    if not actions:
        # Aucune action intéressante ce tour
        print("WAIT")
    else:
        print(";".join(actions))


