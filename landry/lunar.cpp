#include <iostream>
#include <string>
#include <vector>
#include <algorithm>
#include <map>
#include <set>
#include <sstream>
#include <cmath>
#include <queue>

using namespace std;

class Astronaut {
public:
    int type;
    int landingPadId;
    Astronaut() : type(0), landingPadId(0) {}
};

class House {
public:
    int id;
    int type; 
    int x;
    int y;
    vector<int> astronautTypes;
    House() : id(0), type(0), x(0), y(0) {}
}; 

class Tube {
public:
    int bId1;  
    int bId2;
    int capacity;
    Tube() : bId1(0), bId2(0), capacity(0) {}
};

class Teleporter {
public:
    int buildingId1;  
    int buildingId2;
    Teleporter() : buildingId1(0), buildingId2(0) {}
};

class Pod {
public:
    int id;
    vector<int> itinerary;
    Pod() : id(0) {}
};

vector<string> split(const string& s, char delimiter) {
    vector<string> result;
    string token;
    stringstream ss(s);
    while (getline(ss, token, delimiter)) {
        if (!token.empty()) result.push_back(token);
    }
    return result;
}

struct Point {
    float x;
    float y;
};

float distance(Point p1, Point p2) {
    return sqrt((p2.x - p1.x) * (p2.x - p1.x) + (p2.y - p1.y) * (p2.y - p1.y));
}

bool pointOnSegment(Point A, Point B, Point C) {
    float epsilon = 0.0000001;
    float dist = distance(B, A) + distance(A, C) - distance(B, C);
    return (dist > -epsilon && dist < epsilon);
}

int sign(float x) {
    if (x < 0) return -1;
    if (x > 0) return 1;
    return 0;
}

int orientation(Point p1, Point p2, Point p3) {
    float prod = (p3.y - p1.y) * (p2.x - p1.x) - (p2.y - p1.y) * (p3.x - p1.x);
    return sign(prod);
}

bool segmentsIntersect(Point A, Point B, Point C, Point D) {
    return orientation(A, B, C) * orientation(A, B, D) < 0 && 
           orientation(C, D, A) * orientation(C, D, B) < 0;
}

bool canBuildTube(int id1, int id2, map<int, House>& buildings, vector<Tube>& tubes) {
    if (buildings.find(id1) == buildings.end() || buildings.find(id2) == buildings.end()) {
        return false;
    }
    
    Point p1 = {(float)buildings[id1].x, (float)buildings[id1].y};
    Point p2 = {(float)buildings[id2].x, (float)buildings[id2].y};
    
    for (auto& building : buildings) {
        if (building.first != id1 && building.first != id2) {
            Point p = {(float)building.second.x, (float)building.second.y};
            if (pointOnSegment(p, p1, p2)) {
                return false;
            }
        }
    }
    
    for (auto& tube : tubes) {
        Point t1 = {(float)buildings[tube.bId1].x, (float)buildings[tube.bId1].y};
        Point t2 = {(float)buildings[tube.bId2].x, (float)buildings[tube.bId2].y};
        if (segmentsIntersect(p1, p2, t1, t2)) {
            return false;
        }
    }
    
    return true;
}

int calculateTubeCost(int id1, int id2, map<int, House>& buildings) {
    Point p1 = {(float)buildings[id1].x, (float)buildings[id1].y};
    Point p2 = {(float)buildings[id2].x, (float)buildings[id2].y};
    float dist = distance(p1, p2);
    return (int)(dist / 0.1); 
}

vector<int> findModulesOfType(int type, map<int, House>& buildings) {
    vector<int> modules;
    for (auto& building : buildings) {
        if (building.second.type == type) {
            modules.push_back(building.first);
        }
    }
    return modules;
}

vector<int> findLandingPads(map<int, House>& buildings) {
    vector<int> pads;
    for (auto& building : buildings) {
        if (building.second.type == 0) {
            pads.push_back(building.first);
        }
    }
    return pads;
}

int main() {
    map<int, House> buildings; 
    vector<Tube> tubes;  
    map<int, Pod> pods;  
    map<pair<int,int>, bool> teleporters; 
    vector<Astronaut> astronauts;
    
    int nextPodId = 1;
    
    while (1) {
        tubes.clear();
        pods.clear();
        teleporters.clear();
        astronauts.clear();

        int resources;
        cin >> resources; cin.ignore();

        int num_travel_routes;
        cin >> num_travel_routes; cin.ignore();

        for (int i = 0; i < num_travel_routes; i++) {
            int building_id_1, building_id_2, capacity;
            cin >> building_id_1 >> building_id_2 >> capacity; cin.ignore();
            
            if (capacity == 0) {
                int id1 = min(building_id_1, building_id_2);
                int id2 = max(building_id_1, building_id_2);
                teleporters[{id1, id2}] = true;
            } else {
                Tube t;
                t.bId1 = min(building_id_1, building_id_2);
                t.bId2 = max(building_id_1, building_id_2);
                t.capacity = capacity;
                tubes.push_back(t);
            }
        }

        int num_pods;
        cin >> num_pods; cin.ignore();
        for (int i = 0; i < num_pods; i++) {
            string pod_properties;
            getline(cin, pod_properties);
            vector<string> parts = split(pod_properties, ' ');
            Pod p;
            p.id = stoi(parts[0]);
            int pod_size = stoi(parts[1]);
            for (int j = 0; j < pod_size; j++) {
                p.itinerary.push_back(stoi(parts[j + 2])); 
            }
            pods[p.id] = p;
            nextPodId = max(nextPodId, p.id + 1);
        }

        int num_new_buildings;
        cin >> num_new_buildings; cin.ignore();
        for (int i = 0; i < num_new_buildings; i++) {
            string building_properties;
            getline(cin, building_properties);
            vector<string> splitStr = split(building_properties, ' ');
            House h;
            h.type = stoi(splitStr[0]);
            h.id = stoi(splitStr[1]);
            h.x = stoi(splitStr[2]);
            h.y = stoi(splitStr[3]);
            
            if (h.type == 0) {
                int numAstronauts = stoi(splitStr[4]);
                for(int j = 0; j < numAstronauts; j++){
                    Astronaut a;
                    a.type = stoi(splitStr[j + 5]);
                    a.landingPadId = h.id;
                    astronauts.push_back(a);
                    h.astronautTypes.push_back(a.type);
                }    
            }
            
            buildings[h.id] = h;
        }

        
        vector<string> actions;
        
        vector<int> landingPads = findLandingPads(buildings);
        
        for (int padId : landingPads) {
            House& pad = buildings[padId];
            
            
            set<int> uniqueTypes(pad.astronautTypes.begin(), pad.astronautTypes.end());
            
            for (int type : uniqueTypes) {
                vector<int> modules = findModulesOfType(type, buildings);
                
                if (!modules.empty()) {
                
                    int closestModule = modules[0];
                    float minDist = 1e9;
                    
                    for (int moduleId : modules) {
                        Point p1 = {(float)pad.x, (float)pad.y};
                        Point p2 = {(float)buildings[moduleId].x, (float)buildings[moduleId].y};
                        float d = distance(p1, p2);
                        if (d < minDist) {
                            minDist = d;
                            closestModule = moduleId;
                        }
                    }
                    
                    
                    bool tubeExists = false;
                    for (auto& tube : tubes) {
                        if ((tube.bId1 == padId && tube.bId2 == closestModule) ||
                            (tube.bId1 == closestModule && tube.bId2 == padId)) {
                            tubeExists = true;
                            break;
                        }
                    }
                    
                    if (!tubeExists && canBuildTube(padId, closestModule, buildings, tubes)) {
                        int cost = calculateTubeCost(padId, closestModule, buildings);
                        if (resources >= cost) {
                            actions.push_back("TUBE " + to_string(padId) + " " + to_string(closestModule));
                            resources -= cost;
                            
                            Tube newTube;
                            newTube.bId1 = min(padId, closestModule);
                            newTube.bId2 = max(padId, closestModule);
                            newTube.capacity = 1;
                            tubes.push_back(newTube);
                        }
                    }
                    
                
                    bool podExists = false;
                    for (auto& pod : pods) {
                        bool hasPad = false, hasModule = false;
                        for (int stop : pod.second.itinerary) {
                            if (stop == padId) hasPad = true;
                            if (stop == closestModule) hasModule = true;
                        }
                        if (hasPad && hasModule) {
                            podExists = true;
                            break;
                        }
                    }
                    
                    if (!podExists && resources >= 1000) {
                        actions.push_back("POD " + to_string(nextPodId) + " " + 
                                        to_string(padId) + " " + 
                                        to_string(closestModule) + " " + 
                                        to_string(padId));
                        resources -= 1000;
                        nextPodId++;
                    }
                }
            }
        }
        
        if (actions.empty()) {
            cout << "WAIT" << endl;
        } else {
            string output = "";
            for (int i = 0; i < actions.size(); i++) {
                output += actions[i];
                if (i < actions.size() - 1) output += ";";
            }
            cout << output << endl;
        }
    }
}