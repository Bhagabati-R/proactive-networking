"""
pathfinder.py — QoS-aware routing engine.
Uses per-traffic-type cost functions instead of a single latency weight.
"""

import networkx as nx
from network import SOURCE, TARGET, QOS_PROFILES, get_original_attrs


def _apply_costs(G, profile_fn):
    """Stamp a 'cost' attribute on every edge using the QoS profile function."""
    for u, v, d in G.edges(data=True):
        d["cost"] = profile_fn(d)


def find_best_path(G, profile_name):
    """Return (path, cost) using the selected QoS profile."""
    fn = QOS_PROFILES[profile_name]
    _apply_costs(G, fn)
    path = nx.dijkstra_path(G, SOURCE, TARGET, weight="cost")
    cost = nx.dijkstra_path_length(G, SOURCE, TARGET, weight="cost")
    return path, cost


def reroute_around(G, blocked_edge, profile_name):
    """Block an edge (inflate cost) and reroute using the same QoS profile."""
    u, v = blocked_edge
    original = get_original_attrs(u, v)
    G[u][v]["cost"] = 9999

    path = nx.dijkstra_path(G, SOURCE, TARGET, weight="cost")
    cost = nx.dijkstra_path_length(G, SOURCE, TARGET, weight="cost")

    # Restore
    fn = QOS_PROFILES[profile_name]
    G[u][v]["cost"] = fn(original)
    return path, cost


def self_heal(G, failed_edge, profile_name):
    """Remove failed edge, find last-resort path, re-add as ghost."""
    u, v = failed_edge
    G.remove_edge(u, v)

    fn = QOS_PROFILES[profile_name]
    _apply_costs(G, fn)

    if nx.has_path(G, SOURCE, TARGET):
        path = nx.dijkstra_path(G, SOURCE, TARGET, weight="cost")
        cost = nx.dijkstra_path_length(G, SOURCE, TARGET, weight="cost")
        partitioned = False
    else:
        path, cost, partitioned = [], None, True

    G.add_edge(u, v, latency=0, bandwidth=0, jitter=0, reliability=0, cost=9999)
    return path, cost, partitioned


def path_edges(path):
    return list(zip(path[:-1], path[1:]))
