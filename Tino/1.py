import sys
import math
from collections import deque

building_positions = {}      
building_type = {}           
module_type = {}             
landing_astronaut_types = {} 
all_buildings = set()

def orientation(ax, ay, bx, by, cx, cy):
    val = (bx - ax) * (cy - ay) - (by - ay) * (cx - ax)
    if val > 0: return 1
    if val < 0: return -1
    return 0

def point_on_segment(px, py, ax, ay, bx, by):
    if orientation(ax, ay, bx, by, px, py) != 0:
        return False
    return min(ax, bx) <= px <= max(ax, bx) and min(ay, by) <= py <= max(ay, by)

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
    if o1 == 0 and point_on_segment(cx, cy, ax, ay, bx, by): return True
    if o2 == 0 and point_on_segment(dx, dy, ax, ay, bx, by): return True
    if o3 == 0 and point_on_segment(ax, ay, cx, cy, dx, dy): return True
    if o4 == 0 and point_on_segment(bx, by, cx, cy, dx, dy): return True
    return False

def tube_is_valid(u, v, existing_tubes, degree, max_degree=5):
    if u not in building_positions or v not in building_positions:
        return False
    if degree.get(u,0) >= max_degree or degree.get(v,0) >= max_degree:
        return False
    pu, pv = building_positions[u], building_positions[v]
    for a,b in existing_tubes:
        if a in (u,v) or b in (u,v): continue
        pa, pb = building_positions.get(a), building_positions.get(b)
        if pa is None or pb is None: continue
        if segments_intersect(pu,pv,pa,pb): return False
    for w in all_buildings:
        if w in (u,v): continue
        pw = building_positions.get(w)
        if pw is None: continue
        if point_on_segment(pw[0], pw[1], pu[0], pu[1], pv[0], pv[1]): return False
    return True

def tube_cost(u, v):
    if u not in building_positions or v not in building_positions: return 10**9
    x1,y1 = building_positions[u]
    x2,y2 = building_positions[v]
    return int(math.hypot(x2-x1, y2-y1)*10)  # 0.1 km -> 1 ressource

# ============================================
# BFS pour astronautes
# ============================================

def bfs_shortest_route(start, graph, targets):
    """Retourne le chemin BFS le plus court vers un des targets"""
    visited = set()
    queue = deque([(start, [start])])
    while queue:
        node, path = queue.popleft()
        if node in visited: continue
        visited.add(node)
        if node in targets:
            return path
        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                queue.append((neighbor, path + [neighbor]))
    return None

MAX_TUBES_PER_BUILDING = 5
MAX_NEW_TUBES_PER_TURN = 6
MAX_NEW_PODS_PER_TURN = 2
POD_COST = 1000

while True:
    resources = int(input())
    num_travel_routes = int(input())
    routes = []
    existing_tubes = []
    degree = {}
    graph = {}
    for _ in range(num_travel_routes):
        b1,b2,_ = map(int,input().split())
        routes.append((b1,b2))
        existing_tubes.append((b1,b2))
        degree[b1] = degree.get(b1,0)+1
        degree[b2] = degree.get(b2,0)+1
        graph.setdefault(b1, []).append(b2)
        graph.setdefault(b2, []).append(b1)
        all_buildings.add(b1)
        all_buildings.add(b2)

    num_pods = int(input())
    pods_serving = set()
    existing_pod_ids = set()
    for _ in range(num_pods):
        parts = input().split()
        if len(parts)<2: continue
        try: pod_id = int(parts[0]); existing_pod_ids.add(pod_id)
        except: pod_id=None
        for token in parts[2:]:
            try: bid=int(token); pods_serving.add(bid)
            except: pass
    pod_id_counter = 0
    while pod_id_counter in existing_pod_ids: pod_id_counter+=1

    num_new_buildings = int(input())
    new_buildings=[]
    for _ in range(num_new_buildings):
        parts = input().split()
        ints = [int(x) for x in parts if x.isdigit() or (x[0]=="-" and x[1:].isdigit())]
        if not ints: continue
        first = ints[0]
        if first==0 and len(ints)>=5: # landing
            building_id=ints[1]; x=ints[2]; y=ints[3]
            astro_types = ints[5:5+ints[4]]
            building_positions[building_id]=(x,y)
            building_type[building_id]="landing"
            landing_astronaut_types[building_id]=astro_types
        elif first>0 and len(ints)>=4: # module
            mtype=ints[0]; building_id=ints[1]; x=ints[2]; y=ints[3]
            building_positions[building_id]=(x,y)
            building_type[building_id]="module"
            module_type[building_id]=mtype
        else:
            continue
        new_buildings.append(building_id)
        all_buildings.add(building_id)

    actions=[]
    new_tubes_this_turn=0
    remaining_resources=resources

    for b in new_buildings:
        if new_tubes_this_turn>=MAX_NEW_TUBES_PER_TURN or remaining_resources<=0: break
        candidates=[]
        if building_type[b]=="landing":
            types_needed = landing_astronaut_types.get(b,[])
            candidates = [m for m,t in module_type.items() if t in types_needed]
        elif building_type[b]=="module":
            mtype=module_type.get(b)
            candidates=[l for l,types in landing_astronaut_types.items() if mtype in types]
        if not candidates: candidates = list(all_buildings)
        best_neighbor=None; best_cost=10**9
        for c in candidates:
            if c==b: continue
            if degree.get(c,0)>=MAX_TUBES_PER_BUILDING: continue
            cost=tube_cost(b,c)
            if cost>remaining_resources: continue
            if not tube_is_valid(b,c,existing_tubes,degree): continue
            if cost<best_cost: best_neighbor=c; best_cost=cost
        if best_neighbor:
            actions.append(f"TUBE {b} {best_neighbor}")
            existing_tubes.append((b,best_neighbor))
            degree[b]=degree.get(b,0)+1
            degree[best_neighbor]=degree.get(best_neighbor,0)+1
            graph.setdefault(b,[]).append(best_neighbor)
            graph.setdefault(best_neighbor,[]).append(b)
            remaining_resources-=best_cost
            new_tubes_this_turn+=1

    pods_created=0
    for landing_id in [b for b in all_buildings if building_type.get(b)=="landing"]:
        targets=[b for b in all_buildings if building_type.get(b)=="module" and b not in pods_serving]
        if not targets: continue
        path=bfs_shortest_route(landing_id,graph,targets)
        if not path or len(path)<2: continue
        if remaining_resources>=POD_COST and pods_created<MAX_NEW_PODS_PER_TURN:
            route_str=f"{path[0]} {path[1]} {path[0]} {path[1]}"
            actions.append(f"POD {pod_id_counter} {route_str}")
            pods_serving.update(path[:2])
            pod_id_counter+=1
            remaining_resources-=POD_COST
            pods_created+=1

    if not actions: print("WAIT")
    else: print(";".join(actions))
