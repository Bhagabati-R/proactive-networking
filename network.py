"""
network.py — 6-node mesh with multi-weight edges.
Each edge has: latency (ms), bandwidth (Mbps), jitter (ms), reliability (0-1)
"""

import networkx as nx

SOURCE = "R1"
TARGET = "R6"

# (node_a, node_b, latency, bandwidth, jitter, reliability)
EDGE_LIST = [
    ("R1", "R2", 10,  1000, 1,  0.99),
    ("R1", "R3", 15,  500,  3,  0.97),
    ("R2", "R4", 12,  800,  2,  0.98),
    ("R2", "R3", 5,   300,  5,  0.95),
    ("R3", "R5", 20,  600,  4,  0.96),
    ("R4", "R5", 8,   900,  1,  0.99),
    ("R4", "R6", 25,  400,  6,  0.94),
    ("R5", "R6", 10,  750,  2,  0.98),
    ("R3", "R4", 18,  550,  3,  0.97),
]

# QoS profiles — weight formula per traffic type
# Each returns a "cost" value; Dijkstra picks the lowest cost path
QOS_PROFILES = {
    "🎮 Gaming":          lambda e: e["latency"] * 1.0,
    "📹 Video Call":      lambda e: e["latency"] * 0.6 + e["jitter"] * 0.4,
    "🎬 Netflix / VOD":   lambda e: (1 / e["bandwidth"]) * 800 + e["latency"] * 0.2,
    "📁 File Transfer":   lambda e: (1 / e["bandwidth"]) * 1000,
    "🏥 Critical / IoT":  lambda e: (1 - e["reliability"]) * 1000 + e["latency"] * 0.3,
}


def build_graph():
    G = nx.Graph()
    G.add_nodes_from(["R1", "R2", "R3", "R4", "R5", "R6"])
    for u, v, lat, bw, jit, rel in EDGE_LIST:
        G.add_edge(u, v, latency=lat, bandwidth=bw, jitter=jit, reliability=rel)
    return G


def get_fixed_layout(G):
    return nx.spring_layout(G, seed=42)


def get_original_attrs(u, v):
    for a, b, lat, bw, jit, rel in EDGE_LIST:
        if frozenset([a, b]) == frozenset([u, v]):
            return dict(latency=lat, bandwidth=bw, jitter=jit, reliability=rel)
    return None
