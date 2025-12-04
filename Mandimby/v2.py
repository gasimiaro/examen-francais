import sys
import math
from collections import deque

building_positions = {}
building_type = {}
module_type = {}
landing_astronaut_types = {}
all_buildings = set()
turn_number = 0

def orientation(ax, ay, bx, by, cx, cy):
    value = (bx - ax) * (cy - ay) - (by - ay) * (cx - ax)
    if value > 0:
        return 1
    if value < 0:
        return -1
    return 0

def point_on_segment(px, py, ax, ay, bx, by):
    if orientation(ax, ay, bx, by, px, py) != 0:
        return False
    return (min(ax, bx) <= px <= max(ax, bx) and min(ay, by) <= py <= max(ay, by))

def segments_intersect(a, b, c, d):
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

def tube_is_geometrically_valid(u, v, existing_tubes, degree, max_deg=5):
    if u not in building_positions or v not in building_positions:
        return False
    pu = building_positions[u]
    pv = building_positions[v]
    if degree.get(u, 0) >= max_deg or degree.get(v, 0) >= max_deg:
        return False
    for a, b in existing_tubes:
        if a in (u, v) or b in (u, v):
            continue
        pa = building_positions.get(a)
        pb = building_positions.get(b)
        if pa is None or pb is None:
            continue
        if segments_intersect(pu, pv, pa, pb):
            return False
    for w in all_buildings:
        if w in (u, v):
            continue
        pw = building_positions.get(w)
        if pw is None:
            continue
        if point_on_segment(pw[0], pw[1], pu[0], pu[1], pv[0], pv[1]):
            return False
    return True

def tube_construction_cost(u, v):
    if u not in building_positions or v not in building_positions:
        return 10**9
    x1, y1 = building_positions[u]
    x2, y2 = building_positions[v]
    dist = math.hypot(x2 - x1, y2 - y1)
    return int(dist * 10)

def build_adjacency(routes, teleports):
    adj = {}
    for b in all_buildings:
        adj[b] = []
    for b1, b2, cap in routes:
        if cap > 0:
            adj[b1].append((b2, 1))
            adj[b2].append((b1, 1))
        else:
            adj[b1].append((b2, 0))
    return adj

def bfs_distances_from(start, adj):
    dist = {b: 10**9 for b in adj}
    dist[start] = 0
    q = deque([start])
    while q:
        u = q.popleft()
        for v, w in adj.get(u, []):
            new_dist = dist[u] + w
            if new_dist < dist[v]:
                dist[v] = new_dist
                if w == 0:
                    q.appendleft(v)
                else:
                    q.append(v)
    return dist

def get_modules_by_type():
    modules_by_type = {}
    for bid, btype in building_type.items():
        if btype == "module":
            mtype = module_type.get(bid)
            if mtype is not None:
                if mtype not in modules_by_type:
                    modules_by_type[mtype] = []
                modules_by_type[mtype].append(bid)
    return modules_by_type

def find_best_tube_candidate(remaining_resources, degree, existing_tubes):
    best = None
    best_score = -1
    best_cost = 0
    existing_set = set()
    for a, b in existing_tubes:
        existing_set.add((a, b))
        existing_set.add((b, a))
    landings = [b for b in all_buildings if building_type.get(b) == "landing"]
    modules = [b for b in all_buildings if building_type.get(b) == "module"]
    for landing in landings:
        wanted_types = landing_astronaut_types.get(landing, [])
        for mod in modules:
            if (landing, mod) in existing_set:
                continue
            mtype = module_type.get(mod)
            if mtype not in wanted_types:
                continue
            if not tube_is_geometrically_valid(landing, mod, existing_tubes, degree):
                continue
            cost = tube_construction_cost(landing, mod)
            if cost > remaining_resources:
                continue
            score = 10000.0 / max(cost, 1)
            if score > best_score:
                best_score = score
                best = (landing, mod)
                best_cost = cost
    if best:
        return best, best_cost
    for b1 in all_buildings:
        if b1 not in building_positions:
            continue
        for b2 in all_buildings:
            if b2 <= b1 or b2 not in building_positions:
                continue
            if (b1, b2) in existing_set:
                continue
            if not tube_is_geometrically_valid(b1, b2, existing_tubes, degree):
                continue
            cost = tube_construction_cost(b1, b2)
            if cost > remaining_resources:
                continue
            score = 1000.0 / max(cost, 1)
            if score > best_score:
                best_score = score
                best = (b1, b2)
                best_cost = cost
    return best, best_cost

MAX_TUBES_PER_BUILDING = 5
POD_COST = 1000
TELEPORT_COST = 5000

while True:
    turn_number += 1
    resources = int(input())
    num_travel_routes = int(input())
    routes = []
    existing_tubes = []
    degree = {}
    teleports = set()
    for _ in range(num_travel_routes):
        b1, b2, capacity = [int(j) for j in input().split()]
        routes.append((b1, b2, capacity))
        if capacity > 0:
            existing_tubes.append((b1, b2))
        else:
            teleports.add((b1, b2))
        all_buildings.add(b1)
        all_buildings.add(b2)
        degree[b1] = degree.get(b1, 0) + 1
        degree[b2] = degree.get(b2, 0) + 1
    num_pods = int(input())
    pods_serving = set()
    existing_pod_ids = set()
    pod_routes = {}
    for _ in range(num_pods):
        parts = input().split()
        if len(parts) < 3:
            continue
        pod_id = int(parts[0])
        existing_pod_ids.add(pod_id)
        route_buildings = [int(x) for x in parts[2:]]
        pod_routes[pod_id] = route_buildings
        for bid in route_buildings:
            pods_serving.add(bid)
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
    actions = []
    remaining_resources = resources
    MAX_TUBES_THIS_TURN = 10
    tubes_created = 0
    for b in new_buildings:
        if tubes_created >= MAX_TUBES_THIS_TURN:
            break
        if remaining_resources < 100:
            break
        if b not in building_positions:
            continue
        best_neighbor = None
        best_cost = 0
        best_dist2 = None
        bx, by = building_positions[b]
        preferred = []
        b_type = building_type.get(b)
        if b_type == "landing":
            wanted = landing_astronaut_types.get(b, [])
            for other in all_buildings:
                if other == b:
                    continue
                if building_type.get(other) == "module" and module_type.get(other) in wanted:
                    preferred.append(other)
        elif b_type == "module":
            mtype = module_type.get(b)
            for landing_id, types in landing_astronaut_types.items():
                if mtype in types:
                    preferred.append(landing_id)
        candidates = preferred if preferred else list(all_buildings)
        existing_set = set((a, c) for a, c in existing_tubes) | set((c, a) for a, c in existing_tubes)
        for other in candidates:
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
            if best_neighbor is None or dist2 < best_dist2:
                best_neighbor = other
                best_cost = cost
                best_dist2 = dist2
        if best_neighbor is not None:
            actions.append(f"TUBE {b} {best_neighbor}")
            existing_tubes.append((b, best_neighbor))
            degree[b] = degree.get(b, 0) + 1
            degree[best_neighbor] = degree.get(best_neighbor, 0) + 1
            remaining_resources -= best_cost
            tubes_created += 1
    tubes_with_pods = set()
    for pid, route in pod_routes.items():
        for i in range(len(route) - 1):
            a, b = route[i], route[i+1]
            tubes_with_pods.add((min(a, b), max(a, b)))
    tubes_needing_pods = []
    for b1, b2, cap in routes:
        if cap > 0:
            key = (min(b1, b2), max(b1, b2))
            if key not in tubes_with_pods:
                priority = 0
                if building_type.get(b1) == "landing" or building_type.get(b2) == "landing":
                    priority = 10
                tubes_needing_pods.append((priority, b1, b2))
    tubes_needing_pods.sort(reverse=True)
    MAX_PODS_THIS_TURN = 5
    pods_created = 0
    for priority, b1, b2 in tubes_needing_pods:
        if pods_created >= MAX_PODS_THIS_TURN:
            break
        if remaining_resources < POD_COST:
            break
        route_str = f"{b1} {b2} {b1} {b2} {b1} {b2} {b1} {b2}"
        actions.append(f"POD {pod_id_counter} {route_str}")
        pod_id_counter += 1
        while pod_id_counter in existing_pod_ids:
            pod_id_counter += 1
        pods_created += 1
        remaining_resources -= POD_COST
        tubes_with_pods.add((min(b1, b2), max(b1, b2)))
    if remaining_resources > 3000 and turn_number > 3:
        for b1, b2, cap in routes:
            if cap > 0 and cap < 3:
                is_important = (building_type.get(b1) == "landing" or building_type.get(b2) == "landing")
                if is_important:
                    upgrade_cost = tube_construction_cost(b1, b2) * (cap + 1)
                    if upgrade_cost <= remaining_resources:
                        actions.append(f"UPGRADE {b1} {b2}")
                        remaining_resources -= upgrade_cost
                        break
    if remaining_resources > TELEPORT_COST and turn_number > 10:
        landings = [b for b in all_buildings if building_type.get(b) == "landing"]
        modules_list = [b for b in all_buildings if building_type.get(b) == "module"]
        buildings_with_teleport = set()
        for a, b in teleports:
            buildings_with_teleport.add(a)
            buildings_with_teleport.add(b)
        best_teleport = None
        best_dist = 0
        for landing in landings:
            if landing in buildings_with_teleport:
                continue
            for mod in modules_list:
                if mod in buildings_with_teleport:
                    continue
                if landing not in building_positions or mod not in building_positions:
                    continue
                lx, ly = building_positions[landing]
                mx, my = building_positions[mod]
                dist = math.hypot(mx - lx, my - ly)
                if dist > best_dist:
                    best_dist = dist
                    best_teleport = (landing, mod)
        if best_teleport and best_dist > 50:
            actions.append(f"TELEPORT {best_teleport[0]} {best_teleport[1]}")
            remaining_resources -= TELEPORT_COST
    if not actions:
        print("WAIT")
    else:
        print(";".join(actions))
