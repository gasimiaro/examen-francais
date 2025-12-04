import sys
import math
from collections import deque, defaultdict

"""
Selenia City – Version Avancée avec Simulation + Scoring
=========================================================

Méthodes implémentées :
1. BFS pour distances dans le graphe (tubes=1, téléporteurs=0)
2. Simulation naïve du flux d'astronautes
3. Détection des goulots d'étranglement
4. Génération de candidats d'actions avec scoring
5. Pods multi-directions sur tous les tubes importants
6. Upgrades intelligents des tubes saturés
7. Téléporteurs stratégiques en fin de partie
"""

# ====================================================================================
# 1. Structures de données PERSISTANTES
# ====================================================================================

building_positions: dict[int, tuple[int, int]] = {}
building_type: dict[int, str] = {}  # "landing" ou "module"
module_type: dict[int, int] = {}
landing_astronaut_types: dict[int, list[int]] = {}
all_buildings: set[int] = set()
turn_number = 0

# ====================================================================================
# 2. Fonctions géométriques
# ====================================================================================

def orientation(ax, ay, bx, by, cx, cy) -> int:
    value = (bx - ax) * (cy - ay) - (by - ay) * (cx - ax)
    return 1 if value > 0 else (-1 if value < 0 else 0)

def point_on_segment(px, py, ax, ay, bx, by) -> bool:
    if orientation(ax, ay, bx, by, px, py) != 0:
        return False
    return (min(ax, bx) <= px <= max(ax, bx) and min(ay, by) <= py <= max(ay, by))

def segments_intersect(a, b, c, d) -> bool:
    ax, ay = a
    bx, by = b
    cx, cy = c
    dx, dy = d
    o1 = orientation(ax, ay, bx, by, cx, cy)
    o2 = orientation(ax, ay, bx, by, dx, dy)
    o3 = orientation(cx, cy, dx, dy, ax, ay)
    o4 = orientation(cx, cy, dx, dy, bx, by)
    if o1 != 0 and o2 != 0 and o3 != 0 and o4 != 0:
        if (o1 != o2) and (o3 != o4):
            return True
    if o1 == 0 and point_on_segment(cx, cy, ax, ay, bx, by):
        return True
    if o2 == 0 and point_on_segment(dx, dy, ax, ay, bx, by):
        return True
    if o3 == 0 and point_on_segment(ax, ay, cx, cy, dx, dy):
        return True
    if o4 == 0 and point_on_segment(bx, by, cx, cy, dx, dy):
        return True
    return False

def tube_is_geometrically_valid(u: int, v: int, existing_tubes: list, degree: dict, max_deg: int = 5) -> bool:
    if u not in building_positions or v not in building_positions:
        return False
    pu, pv = building_positions[u], building_positions[v]
    if degree.get(u, 0) >= max_deg or degree.get(v, 0) >= max_deg:
        return False
    for a, b in existing_tubes:
        if a in (u, v) or b in (u, v):
            continue
        pa, pb = building_positions.get(a), building_positions.get(b)
        if pa and pb and segments_intersect(pu, pv, pa, pb):
            return False
    for w in all_buildings:
        if w in (u, v):
            continue
        pw = building_positions.get(w)
        if pw and point_on_segment(pw[0], pw[1], pu[0], pu[1], pv[0], pv[1]):
            return False
    return True

def tube_construction_cost(u: int, v: int) -> int:
    if u not in building_positions or v not in building_positions:
        return 10**9
    x1, y1 = building_positions[u]
    x2, y2 = building_positions[v]
    return int(math.hypot(x2 - x1, y2 - y1) * 10)

# ====================================================================================
# 3. BFS et calcul des distances
# ====================================================================================

def build_adjacency(routes: list) -> dict:
    """Construit le graphe d'adjacence. tubes=poids 1, téléporteurs=poids 0."""
    adj = defaultdict(list)
    for b1, b2, cap in routes:
        weight = 1 if cap > 0 else 0  # téléporteur = instantané
        adj[b1].append((b2, weight))
        adj[b2].append((b1, weight))
    return adj

def bfs_distances_from(start: int, adj: dict) -> dict:
    """BFS depuis start, renvoie dist[b] = nb minimal de tubes."""
    dist = {b: 10**9 for b in all_buildings}
    dist[start] = 0
    q = deque([start])
    while q:
        u = q.popleft()
        for v, w in adj.get(u, []):
            new_dist = dist[u] + w
            if new_dist < dist.get(v, 10**9):
                dist[v] = new_dist
                if w == 0:
                    q.appendleft(v)
                else:
                    q.append(v)
    return dist

def get_modules_by_type() -> dict:
    """Renvoie {type: [building_ids]}."""
    result = defaultdict(list)
    for bid, btype in building_type.items():
        if btype == "module":
            mtype = module_type.get(bid)
            if mtype is not None:
                result[mtype].append(bid)
    return result

def compute_min_distance_to_module_type(landing_id: int, target_type: int, adj: dict) -> int:
    """Distance minimale d'une aire d'atterrissage à un module du type voulu."""
    modules_of_type = [b for b in all_buildings 
                       if building_type.get(b) == "module" and module_type.get(b) == target_type]
    if not modules_of_type:
        return 10**9
    dist = bfs_distances_from(landing_id, adj)
    return min(dist.get(m, 10**9) for m in modules_of_type)

# ====================================================================================
# 4. Simulation naïve du flux d'astronautes
# ====================================================================================

def estimate_astronaut_flow(adj: dict, routes: list) -> dict:
    """
    Estime le flux d'astronautes sur chaque tube.
    Renvoie tube_flow[(min(a,b), max(a,b))] = nb estimé d'astronautes/jour.
    """
    tube_flow = defaultdict(int)
    modules_by_type = get_modules_by_type()
    
    for landing_id, astro_types in landing_astronaut_types.items():
        if landing_id not in building_positions:
            continue
        
        # Compter les astronautes par type
        type_counts = defaultdict(int)
        for t in astro_types:
            type_counts[t] += 1
        
        # Pour chaque type, trouver le module le plus proche et tracer le chemin
        for atype, count in type_counts.items():
            targets = modules_by_type.get(atype, [])
            if not targets:
                continue
            
            dist = bfs_distances_from(landing_id, adj)
            best_module = min(targets, key=lambda m: dist.get(m, 10**9))
            best_dist = dist.get(best_module, 10**9)
            
            if best_dist < 10**9:
                # Estimer le flux : astronautes répartis sur le chemin
                # Simplification : on ajoute count au "flux" de tous les tubes du chemin
                # (approximation grossière mais utile)
                tube_flow[(min(landing_id, best_module), max(landing_id, best_module))] += count
    
    return tube_flow

def find_bottleneck_tubes(routes: list, tube_flow: dict) -> list:
    """Trouve les tubes saturés (flux > capacité × 20 jours)."""
    bottlenecks = []
    for b1, b2, cap in routes:
        if cap <= 0:
            continue
        key = (min(b1, b2), max(b1, b2))
        flow = tube_flow.get(key, 0)
        # Capacité effective = cap pods × 10 passagers × 20 jours (simplifié)
        effective_capacity = cap * 10 * 20
        if flow > effective_capacity * 0.5:  # > 50% de saturation
            bottlenecks.append((b1, b2, cap, flow))
    return bottlenecks

# ====================================================================================
# 5. Génération de candidats d'actions avec scoring
# ====================================================================================

def generate_tube_candidates(remaining_resources: int, degree: dict, existing_tubes: list, adj: dict) -> list:
    """Génère des candidats TUBE avec score."""
    candidates = []
    existing_set = set((a, b) for a, b in existing_tubes) | set((b, a) for a, b in existing_tubes)
    modules_by_type = get_modules_by_type()
    
    for landing_id, astro_types in landing_astronaut_types.items():
        if landing_id not in building_positions:
            continue
        
        # Types uniques demandés par cette aire
        wanted_types = set(astro_types)
        
        for wanted in wanted_types:
            modules = modules_by_type.get(wanted, [])
            for mod in modules:
                if (landing_id, mod) in existing_set:
                    continue
                if not tube_is_geometrically_valid(landing_id, mod, existing_tubes, degree):
                    continue
                cost = tube_construction_cost(landing_id, mod)
                if cost > remaining_resources:
                    continue
                
                # Score : nb astronautes de ce type × inverse de la distance
                nb_astros = astro_types.count(wanted)
                dist = math.hypot(
                    building_positions[landing_id][0] - building_positions[mod][0],
                    building_positions[landing_id][1] - building_positions[mod][1]
                )
                score = nb_astros * 1000 / max(dist, 1) - cost * 0.1
                
                candidates.append({
                    "type": "TUBE",
                    "action": f"TUBE {landing_id} {mod}",
                    "score": score,
                    "cost": cost,
                    "buildings": (landing_id, mod)
                })
    
    return candidates

def generate_upgrade_candidates(remaining_resources: int, routes: list, bottlenecks: list) -> list:
    """Génère des candidats UPGRADE pour les tubes saturés."""
    candidates = []
    
    for b1, b2, cap, flow in bottlenecks:
        upgrade_cost = tube_construction_cost(b1, b2) * (cap + 1)
        if upgrade_cost > remaining_resources:
            continue
        
        # Score basé sur le flux et la saturation
        score = flow * 10 - upgrade_cost * 0.1
        
        candidates.append({
            "type": "UPGRADE",
            "action": f"UPGRADE {b1} {b2}",
            "score": score,
            "cost": upgrade_cost,
            "buildings": (b1, b2)
        })
    
    return candidates

def generate_pod_candidates(remaining_resources: int, routes: list, existing_pod_routes: dict, adj: dict) -> list:
    """Génère des candidats POD avec différentes stratégies."""
    candidates = []
    POD_COST = 1000
    
    if remaining_resources < POD_COST:
        return []
    
    # Tubes déjà couverts par des pods
    covered_tubes = set()
    for pid, route in existing_pod_routes.items():
        for i in range(len(route) - 1):
            a, b = route[i], route[i+1]
            covered_tubes.add((min(a, b), max(a, b)))
    
    # Candidats : tubes non couverts, priorité aux tubes touchant une landing
    for b1, b2, cap in routes:
        if cap <= 0:
            continue
        key = (min(b1, b2), max(b1, b2))
        if key in covered_tubes:
            continue
        
        # Score basé sur l'importance du tube
        score = 100
        if building_type.get(b1) == "landing":
            score += 500
            # Bonus si le landing a beaucoup d'astronautes
            score += len(landing_astronaut_types.get(b1, [])) * 10
        if building_type.get(b2) == "landing":
            score += 500
            score += len(landing_astronaut_types.get(b2, [])) * 10
        
        # Route aller-retour
        route_str = f"{b1} {b2} {b1} {b2} {b1} {b2} {b1} {b2}"
        
        candidates.append({
            "type": "POD",
            "action": f"POD {{pod_id}} {route_str}",
            "score": score,
            "cost": POD_COST,
            "buildings": (b1, b2)
        })
    
    return candidates

def generate_teleport_candidates(remaining_resources: int, routes: list, adj: dict) -> list:
    """Génère des candidats TELEPORT entre zones éloignées."""
    candidates = []
    TELEPORT_COST = 5000
    
    if remaining_resources < TELEPORT_COST:
        return []
    
    # Bâtiments déjà avec téléporteur
    has_teleport = set()
    for b1, b2, cap in routes:
        if cap == 0:
            has_teleport.add(b1)
            has_teleport.add(b2)
    
    landings = [b for b in all_buildings if building_type.get(b) == "landing" and b not in has_teleport]
    modules = [b for b in all_buildings if building_type.get(b) == "module" and b not in has_teleport]
    
    for landing in landings:
        if landing not in building_positions:
            continue
        
        # Trouver un module éloigné (distance BFS >= 3)
        dist = bfs_distances_from(landing, adj)
        
        for mod in modules:
            if mod not in building_positions:
                continue
            bfs_dist = dist.get(mod, 10**9)
            
            if bfs_dist >= 3:  # seulement si vraiment loin
                eucl_dist = math.hypot(
                    building_positions[landing][0] - building_positions[mod][0],
                    building_positions[landing][1] - building_positions[mod][1]
                )
                
                # Score : gain de distance × astronautes potentiels
                mtype = module_type.get(mod)
                astro_count = landing_astronaut_types.get(landing, []).count(mtype) if mtype else 0
                score = (bfs_dist - 1) * astro_count * 50 - TELEPORT_COST * 0.01
                
                if score > 0:
                    candidates.append({
                        "type": "TELEPORT",
                        "action": f"TELEPORT {landing} {mod}",
                        "score": score,
                        "cost": TELEPORT_COST,
                        "buildings": (landing, mod)
                    })
    
    return candidates

# ====================================================================================
# 6. Boucle de jeu principale
# ====================================================================================

MAX_TUBES_PER_BUILDING = 5
POD_COST = 1000
TELEPORT_COST = 5000

while True:
    turn_number += 1
    
    # --------------------------------------------------------------------------
    # 6.1. Lecture des entrées
    # --------------------------------------------------------------------------
    resources = int(input())
    
    num_travel_routes = int(input())
    routes = []
    existing_tubes = []
    degree = {}
    
    for _ in range(num_travel_routes):
        b1, b2, capacity = [int(j) for j in input().split()]
        routes.append((b1, b2, capacity))
        if capacity > 0:
            existing_tubes.append((b1, b2))
        all_buildings.add(b1)
        all_buildings.add(b2)
        degree[b1] = degree.get(b1, 0) + 1
        degree[b2] = degree.get(b2, 0) + 1
    
    num_pods = int(input())
    existing_pod_ids = set()
    existing_pod_routes = {}
    
    for _ in range(num_pods):
        parts = input().split()
        if len(parts) < 3:
            continue
        pod_id = int(parts[0])
        existing_pod_ids.add(pod_id)
        route_buildings = [int(x) for x in parts[2:]]
        existing_pod_routes[pod_id] = route_buildings
    
    pod_id_counter = 1
    while pod_id_counter in existing_pod_ids:
        pod_id_counter += 1
    
    num_new_buildings = int(input())
    new_buildings = []
    
    for _ in range(num_new_buildings):
        parts = input().split()
        ints = [int(t) for t in parts if t.lstrip('-').isdigit()]
        if not ints:
            continue
        
        first = ints[0]
        if first == 0 and len(ints) >= 5:
            building_id = ints[1]
            x, y = ints[2], ints[3]
            num_astronauts = ints[4]
            astro_types = ints[5:5 + num_astronauts]
            building_positions[building_id] = (x, y)
            building_type[building_id] = "landing"
            landing_astronaut_types[building_id] = astro_types
        elif first > 0 and len(ints) >= 4:
            mtype = ints[0]
            building_id = ints[1]
            x, y = ints[2], ints[3]
            building_positions[building_id] = (x, y)
            building_type[building_id] = "module"
            module_type[building_id] = mtype
        else:
            continue
        
        new_buildings.append(building_id)
        all_buildings.add(building_id)
    
    # --------------------------------------------------------------------------
    # 6.2. Analyse du réseau
    # --------------------------------------------------------------------------
    adj = build_adjacency(routes)
    tube_flow = estimate_astronaut_flow(adj, routes)
    bottlenecks = find_bottleneck_tubes(routes, tube_flow)
    
    # --------------------------------------------------------------------------
    # 6.3. Génération et scoring des candidats
    # --------------------------------------------------------------------------
    remaining_resources = resources
    actions = []
    used_buildings = set()  # pour éviter les conflits
    
    # Générer tous les candidats
    all_candidates = []
    all_candidates.extend(generate_tube_candidates(remaining_resources, degree, existing_tubes, adj))
    all_candidates.extend(generate_upgrade_candidates(remaining_resources, routes, bottlenecks))
    all_candidates.extend(generate_pod_candidates(remaining_resources, routes, existing_pod_routes, adj))
    
    # Téléporteurs seulement après le tour 8 et si beaucoup de ressources
    if turn_number > 8 and remaining_resources > TELEPORT_COST * 2:
        all_candidates.extend(generate_teleport_candidates(remaining_resources, routes, adj))
    
    # Trier par score décroissant
    all_candidates.sort(key=lambda c: c["score"], reverse=True)
    
    # --------------------------------------------------------------------------
    # 6.4. Sélection des meilleures actions
    # --------------------------------------------------------------------------
    MAX_ACTIONS = 15
    actions_count = {"TUBE": 0, "UPGRADE": 0, "POD": 0, "TELEPORT": 0}
    MAX_PER_TYPE = {"TUBE": 8, "UPGRADE": 2, "POD": 6, "TELEPORT": 1}
    
    for candidate in all_candidates:
        if len(actions) >= MAX_ACTIONS:
            break
        
        ctype = candidate["type"]
        cost = candidate["cost"]
        
        # Limites par type d'action
        if actions_count[ctype] >= MAX_PER_TYPE[ctype]:
            continue
        
        # Vérifier le budget
        if cost > remaining_resources:
            continue
        
        # Vérifier les conflits de bâtiments (pour TUBE et TELEPORT)
        if ctype in ("TUBE", "TELEPORT"):
            b1, b2 = candidate["buildings"]
            # Pour les tubes, re-vérifier la validité géométrique
            if ctype == "TUBE":
                if not tube_is_geometrically_valid(b1, b2, existing_tubes, degree):
                    continue
        
        # Ajouter l'action
        action_str = candidate["action"]
        if ctype == "POD":
            action_str = action_str.replace("{pod_id}", str(pod_id_counter))
            pod_id_counter += 1
            while pod_id_counter in existing_pod_ids:
                pod_id_counter += 1
        
        actions.append(action_str)
        remaining_resources -= cost
        actions_count[ctype] += 1
        
        # Mettre à jour l'état si nécessaire
        if ctype == "TUBE":
            b1, b2 = candidate["buildings"]
            existing_tubes.append((b1, b2))
            degree[b1] = degree.get(b1, 0) + 1
            degree[b2] = degree.get(b2, 0) + 1
    
    # --------------------------------------------------------------------------
    # 6.5. Actions de fallback : connecter les nouveaux bâtiments
    # --------------------------------------------------------------------------
    existing_set = set((a, b) for a, b in existing_tubes) | set((b, a) for a, b in existing_tubes)
    
    for b in new_buildings:
        if actions_count["TUBE"] >= MAX_PER_TYPE["TUBE"]:
            break
        if remaining_resources < 50:
            break
        if b not in building_positions:
            continue
        
        # Vérifier si déjà connecté
        already_connected = any(b in (a, c) for a, c in existing_tubes)
        if already_connected:
            continue
        
        # Trouver le meilleur voisin
        best_neighbor = None
        best_cost = 0
        best_dist2 = 10**18
        bx, by = building_positions[b]
        
        for other in all_buildings:
            if other == b or other not in building_positions:
                continue
            if (b, other) in existing_set:
                continue
            if not tube_is_geometrically_valid(b, other, existing_tubes, degree):
                continue
            cost = tube_construction_cost(b, other)
            if cost > remaining_resources:
                continue
            ox, oy = building_positions[other]
            dist2 = (ox - bx)**2 + (oy - by)**2
            if dist2 < best_dist2:
                best_neighbor = other
                best_cost = cost
                best_dist2 = dist2
        
        if best_neighbor is not None:
            actions.append(f"TUBE {b} {best_neighbor}")
            existing_tubes.append((b, best_neighbor))
            existing_set.add((b, best_neighbor))
            existing_set.add((best_neighbor, b))
            degree[b] = degree.get(b, 0) + 1
            degree[best_neighbor] = degree.get(best_neighbor, 0) + 1
            remaining_resources -= best_cost
            actions_count["TUBE"] += 1
    
    # --------------------------------------------------------------------------
    # 6.6. Fallback : créer des PODs sur tubes non couverts
    # --------------------------------------------------------------------------
    covered_tubes = set()
    for pid, route in existing_pod_routes.items():
        for i in range(len(route) - 1):
            a, b = route[i], route[i+1]
            covered_tubes.add((min(a, b), max(a, b)))
    
    tubes_needing_pods = []
    for b1, b2, cap in routes:
        if cap > 0:
            key = (min(b1, b2), max(b1, b2))
            if key not in covered_tubes:
                priority = 0
                if building_type.get(b1) == "landing":
                    priority += 100
                if building_type.get(b2) == "landing":
                    priority += 100
                tubes_needing_pods.append((priority, b1, b2))
    
    tubes_needing_pods.sort(reverse=True)
    
    for priority, b1, b2 in tubes_needing_pods:
        if actions_count["POD"] >= MAX_PER_TYPE["POD"]:
            break
        if remaining_resources < POD_COST:
            break
        
        route_str = f"{b1} {b2} {b1} {b2} {b1} {b2} {b1} {b2}"
        actions.append(f"POD {pod_id_counter} {route_str}")
        pod_id_counter += 1
        while pod_id_counter in existing_pod_ids:
            pod_id_counter += 1
        remaining_resources -= POD_COST
        actions_count["POD"] += 1
        covered_tubes.add((min(b1, b2), max(b1, b2)))
    
    # --------------------------------------------------------------------------
    # 6.7. Sortie
    # --------------------------------------------------------------------------
    if not actions:
        print("WAIT")
    else:
        print(";".join(actions))
