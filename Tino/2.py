import sys
import math
from collections import deque, defaultdict

# ============================================
# STRUCTURES PERSISTANTES
# ============================================
building_positions = {}      # building_id -> (x, y)
building_type = {}           # building_id -> "landing"/"module"
module_type = {}             # building_id -> module_type (int)
landing_astronaut_types = {} # landing_id -> [list of astronaut types]
all_buildings = set()
turn_number = 0
month_population = defaultdict(int)  # module_id -> population ce mois
existing_pod_routes = set()  # (start, end) pour éviter doublons

# ============================================
# GÉOMÉTRIE
# ============================================
def orientation(ax, ay, bx, by, cx, cy):
    """Calcule l'orientation du triplet (a, b, c)"""
    val = (bx - ax) * (cy - ay) - (by - ay) * (cx - ax)
    return 1 if val > 0 else (-1 if val < 0 else 0)

def point_on_segment(px, py, ax, ay, bx, by):
    """Vérifie si le point p est sur le segment [a, b]"""
    if orientation(ax, ay, bx, by, px, py) != 0:
        return False
    return min(ax, bx) <= px <= max(ax, bx) and min(ay, by) <= py <= max(ay, by)

def segments_intersect(a, b, c, d):
    """Vérifie si les segments [a,b] et [c,d] se croisent"""
    ax, ay = a
    bx, by = b
    cx, cy = c
    dx, dy = d
    
    o1 = orientation(ax, ay, bx, by, cx, cy)
    o2 = orientation(ax, ay, bx, by, dx, dy)
    o3 = orientation(cx, cy, dx, dy, ax, ay)
    o4 = orientation(cx, cy, dx, dy, bx, by)
    
    # Cas général
    if o1 != 0 and o2 != 0 and o3 != 0 and o4 != 0:
        if o1 != o2 and o3 != o4:
            return True
    
    # Cas colinéaires
    if o1 == 0 and point_on_segment(cx, cy, ax, ay, bx, by):
        return True
    if o2 == 0 and point_on_segment(dx, dy, ax, ay, bx, by):
        return True
    if o3 == 0 and point_on_segment(ax, ay, cx, cy, dx, dy):
        return True
    if o4 == 0 and point_on_segment(bx, by, cx, cy, dx, dy):
        return True
    
    return False

def tube_is_valid(u, v, existing_tubes, degree, max_deg=5):
    """Vérifie qu'un tube peut être construit entre u et v"""
    if u not in building_positions or v not in building_positions:
        return False
    
    # Vérifier le degré maximal
    if degree.get(u, 0) >= max_deg or degree.get(v, 0) >= max_deg:
        return False
    
    pu = building_positions[u]
    pv = building_positions[v]
    
    # Vérifier croisement avec tubes existants
    for a, b in existing_tubes:
        if a in (u, v) or b in (u, v):
            continue
        pa = building_positions[a]
        pb = building_positions[b]
        if segments_intersect(pu, pv, pa, pb):
            return False
    
    # Vérifier qu'aucun bâtiment n'est sur le trajet
    for w in all_buildings:
        if w in (u, v):
            continue
        pw = building_positions[w]
        if point_on_segment(pw[0], pw[1], pu[0], pu[1], pv[0], pv[1]):
            return False
    
    return True

def tube_cost(u, v):
    """Calcule le coût d'un tube entre u et v"""
    x1, y1 = building_positions[u]
    x2, y2 = building_positions[v]
    distance = math.hypot(x2 - x1, y2 - y1)
    return int(distance * 10)

def distance_between(u, v):
    """Distance euclidienne entre deux bâtiments"""
    x1, y1 = building_positions[u]
    x2, y2 = building_positions[v]
    return math.hypot(x2 - x1, y2 - y1)

# ============================================
# PATHFINDING
# ============================================
def bfs_shortest_path(start, graph, targets):
    """BFS pour trouver le chemin le plus court vers un des targets"""
    if not targets:
        return None
    
    visited = set()
    queue = deque([(start, [start])])
    
    while queue:
        node, path = queue.popleft()
        
        if node in visited:
            continue
        visited.add(node)
        
        if node in targets:
            return path
        
        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                queue.append((neighbor, path + [neighbor]))
    
    return None

def find_all_reachable_modules(landing_id, graph, target_type):
    """Trouve tous les modules d'un type donné accessibles depuis un landing"""
    targets = [m for m in all_buildings 
               if building_type.get(m) == "module" and module_type.get(m) == target_type]
    
    reachable = []
    for target in targets:
        path = bfs_shortest_path(landing_id, graph, {target})
        if path:
            reachable.append((target, len(path), path))
    
    return reachable

# ============================================
# GESTION DES PODS
# ============================================
def create_pod_route(start, end, via_points=None):
    """Crée une route de POD en boucle fermée"""
    if via_points:
        route = [start] + via_points + [end, start]
    else:
        route = [start, end, start]
    return route

def pod_route_exists(start, end):
    """Vérifie si un POD dessert déjà cette route"""
    return (start, end) in existing_pod_routes or (end, start) in existing_pod_routes

# ============================================
# STRATÉGIE DE CONSTRUCTION
# ============================================
def build_essential_tubes(new_buildings, existing_tubes, degree, graph, remaining_resources, max_new_tubes=15):
    """Construit les tubes essentiels pour connecter les nouveaux bâtiments"""
    actions = []
    tubes_built = 0
    
    for building_id in new_buildings:
        if tubes_built >= max_new_tubes or remaining_resources <= 0:
            break
        
        # Trouver les meilleurs candidats à connecter
        candidates = []
        
        if building_type.get(building_id) == "landing":
            # Landing -> connecter aux modules de ses types d'astronautes
            astro_types = set(landing_astronaut_types.get(building_id, []))
            candidates = [m for m in all_buildings 
                         if building_type.get(m) == "module" 
                         and module_type.get(m) in astro_types]
        
        elif building_type.get(building_id) == "module":
            # Module -> connecter aux landings qui ont besoin de ce type
            mtype = module_type.get(building_id)
            candidates = [l for l in all_buildings 
                         if building_type.get(l) == "landing" 
                         and mtype in landing_astronaut_types.get(l, [])]
        
        # Si pas de candidats évidents, connecter aux bâtiments proches
        if not candidates:
            candidates = list(all_buildings - {building_id})
        
        # Trier par distance et essayer de construire
        candidates_with_cost = []
        for c in candidates:
            if c == building_id:
                continue
            if degree.get(c, 0) >= 5:
                continue
            if (building_id, c) in existing_tubes or (c, building_id) in existing_tubes:
                continue
            
            cost = tube_cost(building_id, c)
            if cost <= remaining_resources:
                candidates_with_cost.append((c, cost))
        
        # Trier par coût croissant
        candidates_with_cost.sort(key=lambda x: x[1])
        
        # Essayer de construire les tubes les moins chers
        for target, cost in candidates_with_cost:
            if tubes_built >= max_new_tubes or remaining_resources < cost:
                break
            
            if tube_is_valid(building_id, target, existing_tubes, degree):
                actions.append(f"TUBE {building_id} {target}")
                existing_tubes.append((building_id, target))
                degree[building_id] = degree.get(building_id, 0) + 1
                degree[target] = degree.get(target, 0) + 1
                graph.setdefault(building_id, []).append(target)
                graph.setdefault(target, []).append(building_id)
                remaining_resources -= cost
                tubes_built += 1
                break
    
    return actions, remaining_resources

def create_pods_for_landings(graph, remaining_resources, pod_id_counter, max_pods=20):
    """Crée des PODs pour tous les landings"""
    actions = []
    pods_created = 0
    
    # Pour chaque landing
    for landing_id in [b for b in all_buildings if building_type.get(b) == "landing"]:
        if pods_created >= max_pods or remaining_resources < 1000:
            break
        
        # Types d'astronautes de ce landing
        astro_types = set(landing_astronaut_types.get(landing_id, []))
        
        # Pour chaque type d'astronaute
        for astro_type in astro_types:
            if pods_created >= max_pods or remaining_resources < 1000:
                break
            
            # Trouver tous les modules accessibles de ce type
            reachable = find_all_reachable_modules(landing_id, graph, astro_type)
            
            if not reachable:
                continue
            
            # Trier par population (moins peuplé d'abord) puis par distance
            reachable.sort(key=lambda x: (month_population.get(x[0], 0), x[1]))
            
            # Créer des PODs vers les 2-3 modules les moins chargés
            pods_for_this_type = 0
            for module_id, path_length, path in reachable:
                if pods_for_this_type >= 3 or pods_created >= max_pods or remaining_resources < 1000:
                    break
                
                # Vérifier si route existe déjà
                if pod_route_exists(landing_id, module_id):
                    continue
                
                # Créer le POD en boucle fermée
                route = create_pod_route(landing_id, module_id)
                route_str = " ".join(map(str, route))
                
                actions.append(f"POD {pod_id_counter} {route_str}")
                existing_pod_routes.add((landing_id, module_id))
                
                # Mettre à jour la population estimée
                month_population[module_id] += 1
                
                pod_id_counter += 1
                remaining_resources -= 1000
                pods_created += 1
                pods_for_this_type += 1
    
    return actions, remaining_resources, pod_id_counter

def create_teleporters(graph, remaining_resources, max_teleports=3):
    """Crée des téléporteurs pour les longues distances"""
    actions = []
    teleports_created = 0
    teleport_cost = 5000
    
    # Minimum de ressources pour considérer les téléporteurs
    if remaining_resources < teleport_cost * 2:
        return actions, remaining_resources
    
    # Trouver les paires landing-module avec grande distance
    candidates = []
    
    for landing_id in [b for b in all_buildings if building_type.get(b) == "landing"]:
        astro_types = set(landing_astronaut_types.get(landing_id, []))
        
        for module_id in [m for m in all_buildings if building_type.get(m) == "module"]:
            if module_type.get(module_id) not in astro_types:
                continue
            
            dist = distance_between(landing_id, module_id)
            
            # Si distance > 50km, téléporteur peut être intéressant
            if dist > 50:
                # Vérifier si un téléporteur est possible (1 entrée/sortie max)
                # Pour simplifier, on vérifie juste dans le graph actuel
                path = bfs_shortest_path(landing_id, graph, {module_id})
                if not path or len(path) > 3:  # Si pas de chemin ou chemin long
                    candidates.append((landing_id, module_id, dist))
    
    # Trier par distance décroissante (plus long = plus prioritaire)
    candidates.sort(key=lambda x: x[2], reverse=True)
    
    for entrance, exit_id, dist in candidates:
        if teleports_created >= max_teleports or remaining_resources < teleport_cost:
            break
        
        actions.append(f"TELEPORT {entrance} {exit_id}")
        remaining_resources -= teleport_cost
        teleports_created += 1
    
    return actions, remaining_resources

# ============================================
# BOUCLE PRINCIPALE
# ============================================
while True:
    turn_number += 1
    resources = int(input())
    
    # Reset population mensuelle
    month_population.clear()
    
    # ----- LECTURE DES ROUTES EXISTANTES -----
    num_routes = int(input())
    routes = []
    existing_tubes = []
    existing_teleports = []
    degree = {}
    graph = {}
    
    for _ in range(num_routes):
        b1, b2, cap = map(int, input().split())
        
        if cap > 0:  # Tube magnétique
            existing_tubes.append((b1, b2))
            degree[b1] = degree.get(b1, 0) + 1
            degree[b2] = degree.get(b2, 0) + 1
            graph.setdefault(b1, []).append(b2)
            graph.setdefault(b2, []).append(b1)
        else:  # Téléporteur
            existing_teleports.append((b1, b2))
            graph.setdefault(b1, []).append(b2)
        
        routes.append((b1, b2, cap))
        all_buildings.add(b1)
        all_buildings.add(b2)
    
    # ----- LECTURE DES PODS EXISTANTS -----
    num_pods = int(input())
    existing_pod_ids = set()
    
    for _ in range(num_pods):
        parts = list(map(int, input().split()))
        if len(parts) < 3:
            continue
        
        pod_id = parts[0]
        num_stops = parts[1]
        stops = parts[2:2 + num_stops]
        
        existing_pod_ids.add(pod_id)
        
        # Marquer les routes servies
        if len(stops) >= 2:
            existing_pod_routes.add((stops[0], stops[-1]))
    
    # Trouver un pod_id disponible
    pod_id_counter = 1
    while pod_id_counter in existing_pod_ids:
        pod_id_counter += 1
    
    # ----- LECTURE DES NOUVEAUX BÂTIMENTS -----
    num_new_buildings = int(input())
    new_buildings = []
    
    for _ in range(num_new_buildings):
        line = input().split()
        parts = [int(x) for x in line if x.lstrip('-').isdigit()]
        
        if not parts:
            continue
        
        first = parts[0]
        
        if first == 0 and len(parts) >= 5:  # Landing pad
            b_id = parts[1]
            x, y = parts[2], parts[3]
            num_astronauts = parts[4]
            astro_types = parts[5:5 + num_astronauts]
            
            building_positions[b_id] = (x, y)
            building_type[b_id] = "landing"
            landing_astronaut_types[b_id] = astro_types
            new_buildings.append(b_id)
        
        elif first > 0 and len(parts) >= 4:  # Module lunaire
            mtype = parts[0]
            b_id = parts[1]
            x, y = parts[2], parts[3]
            
            building_positions[b_id] = (x, y)
            building_type[b_id] = "module"
            module_type[b_id] = mtype
            new_buildings.append(b_id)
        
        all_buildings.add(b_id)
    
    # ============================================
    # STRATÉGIE DE CONSTRUCTION
    # ============================================
    actions = []
    remaining_resources = resources
    
    # 1. CONSTRUIRE LES TUBES ESSENTIELS
    tube_actions, remaining_resources = build_essential_tubes(
        new_buildings, existing_tubes, degree, graph, remaining_resources
    )
    actions.extend(tube_actions)
    
    # 2. CRÉER DES PODS POUR TOUS LES LANDINGS
    pod_actions, remaining_resources, pod_id_counter = create_pods_for_landings(
        graph, remaining_resources, pod_id_counter
    )
    actions.extend(pod_actions)
    
    # 3. INVESTIR SURPLUS EN TÉLÉPORTEURS (late game)
    if turn_number > 10 and remaining_resources >= 10000:
        teleport_actions, remaining_resources = create_teleporters(
            graph, remaining_resources
        )
        actions.extend(teleport_actions)
    
    # ============================================
    # SORTIE
    # ============================================
    if actions:
        print(";".join(actions), file=sys.stdout, flush=True)
    else:
        print("WAIT", file=sys.stdout, flush=True)
