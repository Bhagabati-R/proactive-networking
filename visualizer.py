"""
visualizer.py — Renders the network graph with QoS-aware edge labels.
Label shown on each edge changes based on what the traffic type cares about.
"""

import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

COLOR_OPTIMAL   = "#27ae60"
COLOR_WARNING   = "orange"
COLOR_CONGESTED = "#e74c3c"
COLOR_REROUTED  = "#2980b9"
COLOR_IDLE      = "#bdc3c7"
COLOR_NODE      = "#2c3e50"
COLOR_BG        = "#f0f4f8"

# What label to show on edges per traffic type
EDGE_LABEL_KEY = {
    "🎮 Gaming":          ("latency",     "ms"),
    "📹 Video Call":      ("jitter",      "ms jitter"),
    "🎬 Netflix / VOD":   ("bandwidth",   "Mbps"),
    "📁 File Transfer":   ("bandwidth",   "Mbps"),
    "🏥 Critical / IoT":  ("reliability", ""),
}


def _legend():
    return [
        mpatches.Patch(color=COLOR_OPTIMAL,   label="Optimal Path"),
        mpatches.Patch(color=COLOR_WARNING,   label="Warning — Near Capacity"),
        mpatches.Patch(color=COLOR_CONGESTED, label="Congested / Failed"),
        mpatches.Patch(color=COLOR_REROUTED,  label="Rerouted Path"),
        mpatches.Patch(color=COLOR_IDLE,      label="Idle Link"),
    ]


def build_figure(G, pos, title,
                 highlight_edges=None, highlight_color=COLOR_OPTIMAL,
                 congested_edges=None, failed_edges=None,
                 warning_edges=None, profile_name="🎮 Gaming"):

    fig, ax = plt.subplots(figsize=(10, 6))
    fig.patch.set_facecolor(COLOR_BG)
    ax.set_facecolor(COLOR_BG)
    ax.set_title(title, fontsize=12, fontweight="bold", pad=14)
    ax.axis("off")

    highlight_set = set(map(frozenset, highlight_edges or []))
    congested_set = set(map(frozenset, congested_edges or []))
    failed_set    = set(map(frozenset, failed_edges    or []))
    warning_set   = set(map(frozenset, warning_edges   or []))

    buckets = {
        COLOR_IDLE:      [], COLOR_CONGESTED: [],
        COLOR_WARNING:   [], highlight_color:  [],
    }
    widths = {k: [] for k in buckets}

    for u, v in G.edges():
        fs = frozenset([u, v])
        if fs in failed_set or fs in congested_set:
            buckets[COLOR_CONGESTED].append((u, v)); widths[COLOR_CONGESTED].append(3.5)
        elif fs in warning_set:
            buckets[COLOR_WARNING].append((u, v));   widths[COLOR_WARNING].append(3.5)
        elif fs in highlight_set:
            buckets[highlight_color].append((u, v)); widths[highlight_color].append(4.0)
        else:
            buckets[COLOR_IDLE].append((u, v));      widths[COLOR_IDLE].append(1.5)

    for color, edgelist in buckets.items():
        if edgelist:
            nx.draw_networkx_edges(G, pos, edgelist=edgelist, ax=ax,
                                   edge_color=color, width=widths[color])

    nx.draw_networkx_nodes(G, pos, ax=ax, node_color=COLOR_NODE, node_size=950)
    nx.draw_networkx_labels(G, pos, ax=ax, font_color="white",
                            font_size=10, font_weight="bold")

    # Edge labels — show the metric that matters for this traffic type
    key, unit = EDGE_LABEL_KEY.get(profile_name, ("latency", "ms"))
    edge_labels = {}
    for u, v, d in G.edges(data=True):
        val = d.get(key, 0)
        if val and val > 0:
            if key == "reliability":
                edge_labels[(u, v)] = f"{val:.0%}"
            elif key == "bandwidth":
                edge_labels[(u, v)] = f"{val}Mbps"
            else:
                edge_labels[(u, v)] = f"{val}{unit}"

    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels,
                                 ax=ax, font_size=8, font_color="#444444")

    ax.legend(handles=_legend(), loc="lower left", fontsize=8, framealpha=0.9)
    plt.tight_layout(pad=1.5)
    return fig
