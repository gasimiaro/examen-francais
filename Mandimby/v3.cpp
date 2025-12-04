#include <bits/stdc++.h>
using namespace std;

using ll = long long;

struct PairHash {
    size_t operator()(const pair<int,int>& p) const noexcept {
        return (uint64_t(p.first) << 32) ^ uint64_t(p.second);
    }
};

struct Candidate {
    string type;
    string action;
    double score;
    int cost;
    pair<int,int> buildings;
};

static unordered_map<int, pair<int,int>> building_positions;
static unordered_map<int, string> building_type;
static unordered_map<int, int> module_type;
static unordered_map<int, vector<int>> landing_astronaut_types;
static unordered_set<int> all_buildings;
static int turn_number = 0;

int orientation(int ax, int ay, int bx, int by, int cx, int cy) {
    long long value = 1LL*(bx - ax) * (cy - ay) - 1LL*(by - ay) * (cx - ax);
    if (value > 0) return 1;
    if (value < 0) return -1;
    return 0;
}

bool point_on_segment(int px, int py, int ax, int ay, int bx, int by) {
    if (orientation(ax, ay, bx, by, px, py) != 0) return false;
    return (min(ax,bx) <= px && px <= max(ax,bx) && min(ay,by) <= py && py <= max(ay,by));
}

bool segments_intersect(pair<int,int> a, pair<int,int> b, pair<int,int> c, pair<int,int> d) {
    int ax = a.first, ay = a.second;
    int bx = b.first, by = b.second;
    int cx = c.first, cy = c.second;
    int dx = d.first, dy = d.second;
    int o1 = orientation(ax, ay, bx, by, cx, cy);
    int o2 = orientation(ax, ay, bx, by, dx, dy);
    int o3 = orientation(cx, cy, dx, dy, ax, ay);
    int o4 = orientation(cx, cy, dx, dy, bx, by);
    if (o1 != 0 && o2 != 0 && o3 != 0 && o4 != 0) {
        if ((o1 != o2) && (o3 != o4)) return true;
    }
    if (o1 == 0 && point_on_segment(cx, cy, ax, ay, bx, by)) return true;
    if (o2 == 0 && point_on_segment(dx, dy, ax, ay, bx, by)) return true;
    if (o3 == 0 && point_on_segment(ax, ay, cx, cy, dx, dy)) return true;
    if (o4 == 0 && point_on_segment(bx, by, cx, cy, dx, dy)) return true;
    return false;
}

bool tube_is_geometrically_valid(int u, int v, const vector<pair<int,int>>& existing_tubes, const unordered_map<int,int>& degree, int max_deg = 5) {
    if (building_positions.find(u) == building_positions.end() || building_positions.find(v) == building_positions.end()) return false;
    auto pu = building_positions[u];
    auto pv = building_positions[v];
    if ((degree.count(u) && degree.at(u) >= max_deg) || (degree.count(v) && degree.at(v) >= max_deg)) return false;
    for (auto &ab : existing_tubes) {
        int a = ab.first, b = ab.second;
        if (a == u || a == v || b == u || b == v) continue;
        if (building_positions.count(a) == 0 || building_positions.count(b) == 0) continue;
        auto pa = building_positions[a];
        auto pb = building_positions[b];
        if (segments_intersect(pu, pv, pa, pb)) return false;
    }
    for (int w : all_buildings) {
        if (w == u || w == v) continue;
        if (building_positions.count(w) == 0) continue;
        auto pw = building_positions[w];
        if (point_on_segment(pw.first, pw.second, pu.first, pu.second, pv.first, pv.second)) return false;
    }
    return true;
}

int tube_construction_cost(int u, int v) {
    if (building_positions.find(u) == building_positions.end() || building_positions.find(v) == building_positions.end()) return 1000000000;
    auto p1 = building_positions[u];
    auto p2 = building_positions[v];
    double dx = double(p2.first - p1.first);
    double dy = double(p2.second - p1.second);
    double d = hypot(dx, dy);
    return int(d * 10.0);
}

unordered_map<int, vector<pair<int,int>>> build_adjacency(const vector<tuple<int,int,int>>& routes) {
    unordered_map<int, vector<pair<int,int>>> adj;
    for (int b : all_buildings) adj[b] = {};
    for (auto &t : routes) {
        int b1,b2,cap;
        tie(b1,b2,cap) = t;
        int weight = (cap > 0 ? 1 : 0);
        adj[b1].push_back({b2, weight});
        adj[b2].push_back({b1, weight});
    }
    return adj;
}

unordered_map<int,int> bfs_distances_from(int start, const unordered_map<int, vector<pair<int,int>>>& adj) {
    unordered_map<int,int> dist;
    for (int b : all_buildings) dist[b] = 1000000000;
    dist[start] = 0;
    deque<int> q;
    q.push_back(start);
    while (!q.empty()) {
        int u = q.front(); q.pop_front();
        auto it = adj.find(u);
        if (it == adj.end()) continue;
        for (auto &vw : it->second) {
            int v = vw.first;
            int w = vw.second;
            int nd = dist[u] + w;
            if (nd < dist[v]) {
                dist[v] = nd;
                if (w == 0) q.push_front(v);
                else q.push_back(v);
            }
        }
    }
    return dist;
}

unordered_map<int, vector<int>> get_modules_by_type() {
    unordered_map<int, vector<int>> result;
    for (auto &p : building_type) {
        int bid = p.first;
        string bt = p.second;
        if (bt == "module") {
            if (module_type.count(bid)) {
                result[module_type[bid]].push_back(bid);
            }
        }
    }
    return result;
}

int compute_min_distance_to_module_type(int landing_id, int target_type, const unordered_map<int, vector<pair<int,int>>>& adj) {
    vector<int> modules_of_type;
    for (int b : all_buildings) {
        if (building_type.count(b) && building_type[b] == "module" && module_type.count(b) && module_type[b] == target_type)
            modules_of_type.push_back(b);
    }
    if (modules_of_type.empty()) return 1000000000;
    auto dist = bfs_distances_from(landing_id, adj);
    int best = 1000000000;
    for (int m : modules_of_type) {
        if (dist.count(m)) best = min(best, dist[m]);
    }
    return best;
}

unordered_map<pair<int,int>, int, PairHash> estimate_astronaut_flow(const unordered_map<int, vector<pair<int,int>>>& adj, const vector<tuple<int,int,int>>& routes) {
    unordered_map<pair<int,int>, int, PairHash> tube_flow;
    auto modules_by_type = get_modules_by_type();

    for (auto &entry : landing_astronaut_types) {
        int landing_id = entry.first;
        auto astro_types = entry.second;
        if (building_positions.count(landing_id) == 0) continue;
        unordered_map<int,int> type_counts;
        for (int t : astro_types) type_counts[t]++;
        for (auto &kv : type_counts) {
            int atype = kv.first;
            int count = kv.second;
            auto it = modules_by_type.find(atype);
            if (it == modules_by_type.end()) continue;
            auto dist = bfs_distances_from(landing_id, adj);
            int best_module = -1;
            int bestd = 1000000000;
            for (int m : it->second) {
                if (dist.count(m) && dist[m] < bestd) {
                    bestd = dist[m];
                    best_module = m;
                }
            }
            if (best_module != -1 && bestd < 1000000000) {
                pair<int,int> key = { min(landing_id, best_module), max(landing_id, best_module) };
                tube_flow[key] += count;
            }
        }
    }
    return tube_flow;
}

vector<tuple<int,int,int,int>> find_bottleneck_tubes(const vector<tuple<int,int,int>>& routes, const unordered_map<pair<int,int>, int, PairHash>& tube_flow) {
    vector<tuple<int,int,int,int>> bottlenecks;
    for (auto &t : routes) {
        int b1,b2,cap;
        tie(b1,b2,cap) = t;
        if (cap <= 0) continue;
        pair<int,int> key = { min(b1,b2), max(b1,b2) };
        int flow = 0;
        auto it = tube_flow.find(key);
        if (it != tube_flow.end()) flow = it->second;
        int effective_capacity = cap * 10 * 20;
        if (flow > effective_capacity * 0.5) {
            bottlenecks.emplace_back(b1,b2,cap,flow);
        }
    }
    return bottlenecks;
}

vector<Candidate> generate_tube_candidates(int remaining_resources, const unordered_map<int,int>& degree, const vector<pair<int,int>>& existing_tubes, const unordered_map<int, vector<pair<int,int>>>& adj) {
    vector<Candidate> candidates;
    unordered_set<pair<int,int>, PairHash> existing_set;
    for (auto &e : existing_tubes) {
        existing_set.insert({e.first, e.second});
        existing_set.insert({e.second, e.first});
    }
    auto modules_by_type = get_modules_by_type();
    for (auto &entry : landing_astronaut_types) {
        int landing_id = entry.first;
        auto astro_types = entry.second;
        if (building_positions.count(landing_id) == 0) continue;
        unordered_set<int> wanted_types(astro_types.begin(), astro_types.end());
        for (int wanted : wanted_types) {
            auto it = modules_by_type.find(wanted);
            if (it == modules_by_type.end()) continue;
            for (int mod : it->second) {
                if (existing_set.count({landing_id, mod})) continue;
                if (!tube_is_geometrically_valid(landing_id, mod, existing_tubes, degree)) continue;
                int cost = tube_construction_cost(landing_id, mod);
                if (cost > remaining_resources) continue;
                int nb_astros = 0;
                for (int t : astro_types) if (t == wanted) nb_astros++;
                auto p1 = building_positions[landing_id];
                auto p2 = building_positions[mod];
                double dist = hypot(double(p1.first - p2.first), double(p1.second - p2.second));
                double score = double(nb_astros) * 1000.0 / max(dist, 1.0) - cost * 0.1;
                Candidate c;
                c.type = "TUBE";
                c.action = "TUBE " + to_string(landing_id) + " " + to_string(mod);
                c.score = score;
                c.cost = cost;
                c.buildings = {landing_id, mod};
                candidates.push_back(c);
            }
        }
    }
    return candidates;
}

vector<Candidate> generate_upgrade_candidates(int remaining_resources, const vector<tuple<int,int,int>>& routes, const vector<tuple<int,int,int,int>>& bottlenecks) {
    vector<Candidate> candidates;
    for (auto &b : bottlenecks) {
        int b1,b2,cap,flow;
        tie(b1,b2,cap,flow) = b;
        int upgrade_cost = tube_construction_cost(b1,b2) * (cap + 1);
        if (upgrade_cost > remaining_resources) continue;
        double score = double(flow) * 10.0 - upgrade_cost * 0.1;
        Candidate c;
        c.type = "UPGRADE";
        c.action = "UPGRADE " + to_string(b1) + " " + to_string(b2);
        c.score = score;
        c.cost = upgrade_cost;
        c.buildings = {b1,b2};
        candidates.push_back(c);
    }
    return candidates;
}

vector<Candidate> generate_pod_candidates(int remaining_resources, const vector<tuple<int,int,int>>& routes, const unordered_map<int, vector<int>>& existing_pod_routes, const unordered_map<int, vector<pair<int,int>>>& adj) {
    vector<Candidate> candidates;
    const int POD_COST = 1000;
    if (remaining_resources < POD_COST) return candidates;
    unordered_set<pair<int,int>, PairHash> covered_tubes;
    for (auto &pr : existing_pod_routes) {
        auto route = pr.second;
        for (size_t i=0;i+1<route.size();++i) {
            int a = route[i], b = route[i+1];
            covered_tubes.insert({min(a,b), max(a,b)});
        }
    }
    for (auto &t : routes) {
        int b1,b2,cap; tie(b1,b2,cap) = t;
        if (cap <= 0) continue;
        pair<int,int> key = {min(b1,b2), max(b1,b2)};
        if (covered_tubes.count(key)) continue;
        int score = 100;
        if (building_type.count(b1) && building_type[b1] == "landing") {
            score += 500;
            score += int(landing_astronaut_types[b1].size()) * 10;
        }
        if (building_type.count(b2) && building_type[b2] == "landing") {
            score += 500;
            score += int(landing_astronaut_types[b2].size()) * 10;
        }
        string route_str = to_string(b1) + " " + to_string(b2) + " " + to_string(b1) + " " + to_string(b2) + " " + to_string(b1) + " " + to_string(b2) + " " + to_string(b1) + " " + to_string(b2);
        Candidate c;
        c.type = "POD";
        c.action = "POD {pod_id} " + route_str;
        c.score = score;
        c.cost = POD_COST;
        c.buildings = {b1,b2};
        candidates.push_back(c);
    }
    return candidates;
}

vector<Candidate> generate_teleport_candidates(int remaining_resources, const vector<tuple<int,int,int>>& routes, const unordered_map<int, vector<pair<int,int>>>& adj) {
    vector<Candidate> candidates;
    const int TELEPORT_COST = 5000;
    if (remaining_resources < TELEPORT_COST) return candidates;
    unordered_set<int> has_teleport;
    for (auto &t : routes) {
        int b1,b2,cap; tie(b1,b2,cap) = t;
        if (cap == 0) { has_teleport.insert(b1); has_teleport.insert(b2); }
    }
    vector<int> landings, modules;
    for (int b : all_buildings) {
        if (building_type.count(b) && building_type[b] == "landing" && !has_teleport.count(b)) landings.push_back(b);
        if (building_type.count(b) && building_type[b] == "module" && !has_teleport.count(b)) modules.push_back(b);
    }
    for (int landing : landings) {
        if (building_positions.count(landing) == 0) continue;
        auto distmap = bfs_distances_from(landing, adj);
        for (int mod : modules) {
            if (building_positions.count(mod) == 0) continue;
            int bfs_dist = distmap.count(mod) ? distmap[mod] : 1000000000;
            if (bfs_dist >= 3) {
                auto p1 = building_positions[landing];
                auto p2 = building_positions[mod];
                double eucl_dist = hypot(double(p1.first - p2.first), double(p1.second - p2.second));
                int mtype = module_type.count(mod) ? module_type[mod] : 0;
                int astro_count = 0;
                if (landing_astronaut_types.count(landing)) {
                    for (int x : landing_astronaut_types[landing]) if (x == mtype) astro_count++;
                }
                double score = double(bfs_dist - 1) * double(astro_count) * 50.0 - TELEPORT_COST * 0.01;
                if (score > 0.0) {
                    Candidate c;
                    c.type = "TELEPORT";
                    c.action = "TELEPORT " + to_string(landing) + " " + to_string(mod);
                    c.score = score;
                    c.cost = TELEPORT_COST;
                    c.buildings = {landing, mod};
                    candidates.push_back(c);
                }
            }
        }
    }
    return candidates;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    const int POD_COST = 1000;
    const int TELEPORT_COST = 5000;

    while (true) {
        ++turn_number;
        int resources;
        if (!(cin >> resources)) return 0;
        int num_travel_routes;
        cin >> num_travel_routes;
        vector<tuple<int,int,int>> routes;
        vector<pair<int,int>> existing_tubes;
        unordered_map<int,int> degree;

        for (int i=0;i<num_travel_routes;++i) {
            int b1,b2,capacity;
            cin >> b1 >> b2 >> capacity;
            routes.emplace_back(b1,b2,capacity);
            if (capacity > 0) existing_tubes.emplace_back(b1,b2);
            all_buildings.insert(b1);
            all_buildings.insert(b2);
            degree[b1] = degree.count(b1) ? degree[b1]+1 : 1;
            degree[b2] = degree.count(b2) ? degree[b2]+1 : 1;
        }

        int num_pods;
        cin >> num_pods;
        unordered_set<int> existing_pod_ids;
        unordered_map<int, vector<int>> existing_pod_routes;
        string line;
        getline(cin, line);

        for (int i=0;i<num_pods;++i) {
            string s;
            getline(cin, s);
            if (s.size() == 0) { --i; continue; }
            stringstream ss(s);
            vector<string> parts;
            string tok;
            while (ss >> tok) parts.push_back(tok);
            if (parts.size() < 3) continue;
            int pod_id = stoi(parts[0]);
            existing_pod_ids.insert(pod_id);
            vector<int> route_buildings;
            for (size_t j=2;j<parts.size();++j) {
                try { route_buildings.push_back(stoi(parts[j])); } catch(...) {}
            }
            existing_pod_routes[pod_id] = route_buildings;
        }

        int pod_id_counter = 1;
        while (existing_pod_ids.count(pod_id_counter)) ++pod_id_counter;

        int num_new_buildings;
        cin >> num_new_buildings;
        getline(cin, line);
        vector<int> new_buildings;

        for (int i=0;i<num_new_buildings;++i) {
            string s;
            getline(cin, s);
            if (s.size() == 0) { --i; continue; }
            stringstream ss(s);
            vector<string> parts;
            string tok;
            while (ss >> tok) parts.push_back(tok);
            vector<int> ints;
            for (auto &t : parts) {
                bool neg = false;
                size_t idx = 0;
                if (t.size()>0 && t[0]=='-') { neg = true; idx = 1; }
                bool allnum=true;
                for (size_t k=idx;k<t.size();++k) if (!isdigit((unsigned char)t[k])) { allnum=false; break;}
                if (allnum) {
                    try { ints.push_back(stoi(t)); } catch(...) {}
                }
            }
            if (ints.empty()) continue;
            int first = ints[0];
            if (first == 0 && (int)ints.size() >= 5) {
                int building_id = ints[1];
                int x = ints[2], y = ints[3];
                int num_astronauts = ints[4];
                vector<int> astro_types;
                for (int k=0;k<num_astronauts && 5+k < (int)ints.size(); ++k) astro_types.push_back(ints[5+k]);
                building_positions[building_id] = {x,y};
                building_type[building_id] = "landing";
                landing_astronaut_types[building_id] = astro_types;
                new_buildings.push_back(building_id);
                all_buildings.insert(building_id);
            } else if (first > 0 && (int)ints.size() >= 4) {
                int mtype = ints[0];
                int building_id = ints[1];
                int x = ints[2], y = ints[3];
                building_positions[building_id] = {x,y};
                building_type[building_id] = "module";
                module_type[building_id] = mtype;
                new_buildings.push_back(building_id);
                all_buildings.insert(building_id);
            } else {
                continue;
            }
        }

        auto adj = build_adjacency(routes);
        auto tube_flow = estimate_astronaut_flow(adj, routes);
        auto bottlenecks = find_bottleneck_tubes(routes, tube_flow);

        int remaining_resources = resources;
        vector<string> actions;
        unordered_set<int> used_buildings;

        vector<Candidate> all_candidates;
        {
            auto v = generate_tube_candidates(remaining_resources, degree, existing_tubes, adj);
            all_candidates.insert(all_candidates.end(), v.begin(), v.end());
        }
        {
            auto v = generate_upgrade_candidates(remaining_resources, routes, bottlenecks);
            all_candidates.insert(all_candidates.end(), v.begin(), v.end());
        }
        {
            auto v = generate_pod_candidates(remaining_resources, routes, existing_pod_routes, adj);
            all_candidates.insert(all_candidates.end(), v.begin(), v.end());
        }

        if (turn_number > 8 && remaining_resources > TELEPORT_COST * 2) {
            auto v = generate_teleport_candidates(remaining_resources, routes, adj);
            all_candidates.insert(all_candidates.end(), v.begin(), v.end());
        }

        sort(all_candidates.begin(), all_candidates.end(), [](const Candidate&a, const Candidate&b){
            return a.score > b.score;
        });

        const int MAX_ACTIONS = 15;
        unordered_map<string,int> actions_count = { {"TUBE",0},{"UPGRADE",0},{"POD",0},{"TELEPORT",0} };
        unordered_map<string,int> MAX_PER_TYPE = { {"TUBE",8},{"UPGRADE",2},{"POD",6},{"TELEPORT",1} };

        for (auto &candidate : all_candidates) {
            if ((int)actions.size() >= MAX_ACTIONS) break;
            string ctype = candidate.type;
            int cost = candidate.cost;
            if (actions_count[ctype] >= MAX_PER_TYPE[ctype]) continue;
            if (cost > remaining_resources) continue;
            if (ctype == "TUBE" || ctype == "TELEPORT") {
                int b1 = candidate.buildings.first;
                int b2 = candidate.buildings.second;
                if (ctype == "TUBE") {
                    if (!tube_is_geometrically_valid(b1, b2, existing_tubes, degree)) continue;
                }
            }
            string action_str = candidate.action;
            if (ctype == "POD") {
                string key = "{pod_id}";
                size_t pos = action_str.find(key);
                if (pos != string::npos) action_str.replace(pos, key.size(), to_string(pod_id_counter));
                pod_id_counter += 1;
                while (existing_pod_ids.count(pod_id_counter)) ++pod_id_counter;
            }
            actions.push_back(action_str);
            remaining_resources -= cost;
            actions_count[ctype] += 1;
            if (ctype == "TUBE") {
                int b1 = candidate.buildings.first;
                int b2 = candidate.buildings.second;
                existing_tubes.emplace_back(b1,b2);
                degree[b1] = degree.count(b1) ? degree[b1]+1 : 1;
                degree[b2] = degree.count(b2) ? degree[b2]+1 : 1;
            }
        }

        unordered_set<pair<int,int>, PairHash> existing_set;
        for (auto &e : existing_tubes) {
            existing_set.insert({e.first, e.second});
            existing_set.insert({e.second, e.first});
        }

        for (int b : new_buildings) {
            if (actions_count["TUBE"] >= MAX_PER_TYPE["TUBE"]) break;
            if (remaining_resources < 50) break;
            if (building_positions.count(b) == 0) continue;
            bool already_connected = false;
            for (auto &ec : existing_tubes) if (ec.first == b || ec.second == b) { already_connected = true; break; }
            if (already_connected) continue;
            int best_neighbor = -1;
            int best_cost = 0;
            long long best_dist2 = (long long)1e18;
            auto pb = building_positions[b];
            for (int other : all_buildings) {
                if (other == b || building_positions.count(other) == 0) continue;
                if (existing_set.count({b, other})) continue;
                if (!tube_is_geometrically_valid(b, other, existing_tubes, degree)) continue;
                int cost = tube_construction_cost(b, other);
                if (cost > remaining_resources) continue;
                auto po = building_positions[other];
                long long dx = po.first - pb.first;
                long long dy = po.second - pb.second;
                long long dist2 = dx*dx + dy*dy;
                if (dist2 < best_dist2) {
                    best_dist2 = dist2;
                    best_neighbor = other;
                    best_cost = cost;
                }
            }
            if (best_neighbor != -1) {
                actions.push_back(string("TUBE ") + to_string(b) + " " + to_string(best_neighbor));
                existing_tubes.emplace_back(b, best_neighbor);
                existing_set.insert({b, best_neighbor});
                existing_set.insert({best_neighbor, b});
                degree[b] = degree.count(b) ? degree[b]+1 : 1;
                degree[best_neighbor] = degree.count(best_neighbor) ? degree[best_neighbor]+1 : 1;
                remaining_resources -= best_cost;
                actions_count["TUBE"] += 1;
            }
        }

        unordered_set<pair<int,int>, PairHash> covered_tubes;
        for (auto &pr : existing_pod_routes) {
            auto route = pr.second;
            for (size_t i=0;i+1<route.size();++i) {
                int a = route[i], b = route[i+1];
                covered_tubes.insert({min(a,b), max(a,b)});
            }
        }

        vector<tuple<int,int,int>> tubes_needing_pods;
        for (auto &t : routes) {
            int b1,b2,cap; tie(b1,b2,cap) = t;
            if (cap > 0) {
                pair<int,int> key = {min(b1,b2), max(b1,b2)};
                if (!covered_tubes.count(key)) {
                    int priority = 0;
                    if (building_type.count(b1) && building_type[b1] == "landing") priority += 100;
                    if (building_type.count(b2) && building_type[b2] == "landing") priority += 100;
                    tubes_needing_pods.emplace_back(priority,b1,b2);
                }
            }
        }

        sort(tubes_needing_pods.begin(), tubes_needing_pods.end(), [](const tuple<int,int,int>&a, const tuple<int,int,int>&b){
            return get<0>(a) > get<0>(b);
        });

        for (auto &t : tubes_needing_pods) {
            int priority = get<0>(t), b1 = get<1>(t), b2 = get<2>(t);
            if (actions_count["POD"] >= 6) break;
            if (remaining_resources < POD_COST) break;
            string route_str = to_string(b1) + " " + to_string(b2) + " " + to_string(b1) + " " + to_string(b2) + " " + to_string(b1) + " " + to_string(b2) + " " + to_string(b1) + " " + to_string(b2);
            actions.push_back("POD " + to_string(pod_id_counter) + " " + route_str);
            pod_id_counter += 1;
            while (existing_pod_ids.count(pod_id_counter)) ++pod_id_counter;
            remaining_resources -= POD_COST;
            actions_count["POD"] += 1;
            covered_tubes.insert({min(b1,b2), max(b1,b2)});
        }

        if (actions.empty()) {
            cout << "WAIT\n";
        } else {
            for (size_t i=0;i<actions.size();++i) {
                if (i) cout << ";";
                cout << actions[i];
            }
            cout << "\n";
        }
        cout.flush();
    }

    return 0;
}
