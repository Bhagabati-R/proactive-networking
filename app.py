"""
app.py — Responsive QoS-aware Streamlit simulation.
Works on phone, tablet, and laptop.

Run:
    python -m streamlit run app.py
"""

import time, copy, random
import streamlit as st
import matplotlib.pyplot as plt

import network, pathfinder, visualizer

st.set_page_config(
    page_title="Proactive Networking Simulator",
    page_icon="🌐",
    layout="centered",   # centered works best across all screen sizes
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
/* ── Global ── */
html, body, [class*="css"] { font-family: 'Segoe UI', sans-serif; }

/* ── Metric cards ── */
.metric-card {
    background: #1a2a3a;
    border-radius: 10px;
    padding: 10px 14px;
    margin: 4px 0;
    color: #e0e8f0;
    font-family: monospace;
    font-size: 13px;
    border-left: 4px solid #2980b9;
}
.metric-card.green  { border-left-color: #27ae60; }
.metric-card.orange { border-left-color: #f39c12; }
.metric-card.red    { border-left-color: #e74c3c; }

/* ── Stage badge ── */
.stage-badge {
    display: inline-block;
    padding: 5px 18px;
    border-radius: 20px;
    font-weight: bold;
    font-size: 14px;
    margin-bottom: 8px;
    color: white;
}

/* ── QoS profile buttons ── */
.qos-card {
    border-radius: 10px;
    padding: 10px 6px;
    text-align: center;
    font-weight: bold;
    font-size: 12px;
    cursor: pointer;
    transition: all 0.2s;
}

/* ── Event log ── */
.log-box {
    background: #0a1520;
    border-radius: 8px;
    padding: 10px;
    max-height: 220px;
    overflow-y: auto;
}
.log-line  { font-family:monospace; font-size:12px; padding:3px 6px;
             border-left:3px solid #2980b9; margin:2px 0;
             color:#aaddff; border-radius:0 4px 4px 0; }
.log-warn  { border-left-color:#f39c12; color:#ffd580; }
.log-error { border-left-color:#e74c3c; color:#ffaaaa; }
.log-ok    { border-left-color:#27ae60; color:#aaffcc; }

/* ── Responsive: stack on small screens ── */
@media (max-width: 640px) {
    .stage-badge { font-size: 12px; padding: 4px 12px; }
    .metric-card { font-size: 11px; padding: 8px 10px; }
    .log-line    { font-size: 11px; }
}
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────
def _init():
    defaults = dict(
        stage=1, auto_play=False,
        packets_sent=0, reroutes=0, uptime_s=0,
        traffic_load=30, event_log=[],
        last_tick=time.time(),
        profile="🎮 Gaming",
    )
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v
_init()

@st.cache_resource
def init_network():
    G   = network.build_graph()
    pos = network.get_fixed_layout(G)
    return G, pos

G_base, pos = init_network()

STAGE_META = {
    1: ("🟢", "Optimal Path",          "#27ae60"),
    2: ("🟠", "Proactive Awareness",   "#e67e22"),
    3: ("🔵", "Congestion Prevention", "#2980b9"),
    4: ("🔴", "Self-Healing",          "#e74c3c"),
}
QOS_INFO = {
    "🎮 Gaming":         ("Latency",     "ms",   "Ultra-low latency"),
    "📹 Video Call":     ("Jitter",      "ms",   "Smooth, no freezing"),
    "🎬 Netflix / VOD":  ("Bandwidth",   "Mbps", "No buffering"),
    "📁 File Transfer":  ("Bandwidth",   "Mbps", "Max throughput"),
    "🏥 Critical / IoT": ("Reliability", "%",    "Never drop"),
}
METRIC_KEY = {
    "🎮 Gaming":"latency","📹 Video Call":"jitter",
    "🎬 Netflix / VOD":"bandwidth","📁 File Transfer":"bandwidth",
    "🏥 Critical / IoT":"reliability",
}

def add_log(msg, level="info"):
    ts = time.strftime("%H:%M:%S")
    st.session_state.event_log.append((ts, msg, level))
    if len(st.session_state.event_log) > 25:
        st.session_state.event_log.pop(0)

def advance_stage():
    st.session_state.stage = (st.session_state.stage % 4) + 1
    s = st.session_state.stage
    p = st.session_state.profile
    if s == 2:
        add_log(f"[{p}] Traffic surge — 87% utilisation on primary link", "warn")
    elif s == 3:
        st.session_state.reroutes += 1
        add_log(f"[{p}] Congestion exceeded — rerouting via QoS", "error")
        add_log(f"[{p}] New path active. Zero packet loss.", "ok")
    elif s == 4:
        add_log(f"[{p}] CRITICAL: R4↔R5 physical failure", "error")
        add_log(f"[{p}] Self-Healing: recalculating...", "warn")
    elif s == 1:
        add_log(f"[{p}] Network restored to optimal state", "ok")

# ── Header ────────────────────────────────────────────────────
st.markdown("""
<h2 style='text-align:center;margin-bottom:0'>🌐 Proactive Networking</h2>
<p style='text-align:center;color:#888;margin-top:4px;font-size:14px'>
Link-Aware Congestion Prevention System
</p>
""", unsafe_allow_html=True)

# ── QoS profile selector ──────────────────────────────────────
st.markdown("#### Select Traffic Type")
profiles      = list(network.QOS_PROFILES.keys())
profile_colors = ["#8e44ad","#2980b9","#e74c3c","#27ae60","#e67e22"]
pcols = st.columns(5)

for i, (col, prof, pc) in enumerate(zip(pcols, profiles, profile_colors)):
    with col:
        active = st.session_state.profile == prof
        bg  = pc if active else "#1a2a3a"
        brd = f"2px solid {pc}"
        st.markdown(
            f'<div style="background:{bg};border:{brd};border-radius:10px;'
            f'padding:8px 4px;text-align:center;font-size:11px;font-weight:bold;'
            f'color:white;min-height:48px;display:flex;align-items:center;'
            f'justify-content:center;">{prof}</div>',
            unsafe_allow_html=True,
        )
        if st.button("✓", key=f"p{i}", use_container_width=True):
            old = st.session_state.profile
            st.session_state.profile = prof
            st.session_state.stage   = 1
            add_log(f"Traffic type: {old} → {prof}", "ok")

st.divider()

# ── Controls ──────────────────────────────────────────────────
cc1, cc2, cc3, cc4 = st.columns(4)
with cc1:
    if st.button("▶ Play", use_container_width=True, type="primary"):
        st.session_state.auto_play = True
        add_log("Auto-play started", "ok")
with cc2:
    if st.button("⏸ Pause", use_container_width=True):
        st.session_state.auto_play = False
with cc3:
    if st.button("⏭ Next", use_container_width=True):
        advance_stage()
with cc4:
    if st.button("🔄 Reset", use_container_width=True):
        for k,v in dict(stage=1,auto_play=False,packets_sent=0,
                        reroutes=0,uptime_s=0,traffic_load=30,event_log=[]).items():
            st.session_state[k] = v
        add_log("Reset", "ok")

speed = st.select_slider("Speed", ["Slow (4s)","Normal (2s)","Fast (1s)"],
                          value="Normal (2s)", label_visibility="collapsed")
delay = {"Slow (4s)":4,"Normal (2s)":2,"Fast (1s)":1}[speed]

# ── Live state ────────────────────────────────────────────────
now = time.time()
st.session_state.uptime_s   += int(now - st.session_state.last_tick)
st.session_state.last_tick   = now
st.session_state.packets_sent += random.randint(80, 220)

stage   = st.session_state.stage
profile = st.session_state.profile

tgt = {1:random.randint(25,45),2:random.randint(82,93),
       3:random.randint(15,35),4:random.randint(10,25)}[stage]
st.session_state.traffic_load = int(st.session_state.traffic_load*0.7 + tgt*0.3)

# ── Stage badge + progress ────────────────────────────────────
emoji, slabel, scolor = STAGE_META[stage]
st.markdown(
    f'<div class="stage-badge" style="background:{scolor}">'
    f'{emoji} Stage {stage}: {slabel}</div>',
    unsafe_allow_html=True,
)
st.progress((stage-1)/4, text=f"Cycle: Stage {stage} of 4")

# ── Network graph ─────────────────────────────────────────────
G = copy.deepcopy(G_base)
optimal_path, _ = pathfinder.find_best_path(G, profile)
stressed_link   = pathfinder.path_edges(optimal_path)[0]

G2 = copy.deepcopy(G_base)
if stage == 1:
    p, _ = pathfinder.find_best_path(G2, profile)
    fig = visualizer.build_figure(G2, pos,
        f"Stage 1 [{profile}]: Optimal Path",
        highlight_edges=pathfinder.path_edges(p),
        highlight_color=visualizer.COLOR_OPTIMAL,
        profile_name=profile)

elif stage == 2:
    p, _ = pathfinder.find_best_path(G2, profile)
    non_s = [e for e in pathfinder.path_edges(p)
             if frozenset(e) != frozenset(stressed_link)]
    fig = visualizer.build_figure(G2, pos,
        f"Stage 2 [{profile}]: Primary Link Warning",
        highlight_edges=non_s,
        highlight_color=visualizer.COLOR_OPTIMAL,
        warning_edges=[stressed_link],
        profile_name=profile)

elif stage == 3:
    p, _ = pathfinder.find_best_path(G2, profile)
    sl   = pathfinder.path_edges(p)[0]
    rp, _ = pathfinder.reroute_around(G2, sl, profile)
    fig = visualizer.build_figure(G2, pos,
        f"Stage 3 [{profile}]: Rerouted Path",
        highlight_edges=pathfinder.path_edges(rp),
        highlight_color=visualizer.COLOR_REROUTED,
        congested_edges=[sl],
        profile_name=profile)

else:
    p, _ = pathfinder.find_best_path(G2, profile)
    sl   = pathfinder.path_edges(p)[0]
    failed = ("R4","R5")
    lr, _, _ = pathfinder.self_heal(G2, failed, profile)
    fig = visualizer.build_figure(G2, pos,
        f"Stage 4 [{profile}]: Self-Healing",
        highlight_edges=pathfinder.path_edges(lr),
        highlight_color=visualizer.COLOR_REROUTED,
        congested_edges=[sl],
        failed_edges=[failed],
        profile_name=profile)

st.pyplot(fig, use_container_width=True)
plt.close(fig)

metric, unit, desc = QOS_INFO[profile]
st.info(f"**{profile}** → optimising for **{metric}** ({unit}) — {desc}")

# ── Metrics row (responsive 4-col) ───────────────────────────
st.divider()
st.markdown("#### 📡 Live Metrics")
m1, m2, m3, m4 = st.columns(4)
tl = st.session_state.traffic_load
tc = "red" if tl>=80 else "orange" if tl>=60 else "green"

with m1:
    st.markdown(f'<div class="metric-card green">📦 Packets<br><b>{st.session_state.packets_sent:,}</b></div>',
                unsafe_allow_html=True)
with m2:
    st.markdown(f'<div class="metric-card purple" style="border-left-color:#8e44ad">🔀 Reroutes<br><b>{st.session_state.reroutes}</b></div>',
                unsafe_allow_html=True)
with m3:
    st.markdown(f'<div class="metric-card">⏱ Uptime<br><b>{st.session_state.uptime_s}s</b></div>',
                unsafe_allow_html=True)
with m4:
    st.markdown(f'<div class="metric-card {tc}">📶 Load<br><b>{tl}%</b></div>',
                unsafe_allow_html=True)

st.progress(tl/100)

# ── Path info + Event log (responsive 2-col on wide, stacked on mobile) ──
st.divider()
pi_col, log_col = st.columns([1, 1])

with pi_col:
    st.markdown("#### 📊 Path Info")
    G3 = copy.deepcopy(G_base)
    cur_path, _ = pathfinder.find_best_path(G3, profile)
    mk = METRIC_KEY[profile]
    st.markdown(f"**Profile:** {profile}")
    st.markdown(f"**Path:** `{' → '.join(cur_path)}`")
    for u, v in pathfinder.path_edges(cur_path):
        d   = G3[u][v]
        val = d.get(mk, "?")
        if mk == "reliability":
            st.markdown(f"- `{u}→{v}` : {val:.0%}")
        elif mk == "bandwidth":
            st.markdown(f"- `{u}→{v}` : {val} Mbps")
        else:
            st.markdown(f"- `{u}→{v}` : {val} ms")

with log_col:
    st.markdown("#### 🖥 Event Log")
    log_html = '<div class="log-box">'
    for ts, msg, lvl in reversed(st.session_state.event_log[-12:]):
        css = {"warn":"log-warn","error":"log-error","ok":"log-ok"}.get(lvl,"log-line")
        log_html += f'<div class="log-line {css}">[{ts}] {msg}</div>'
    if not st.session_state.event_log:
        log_html += '<div style="color:#445;font-family:monospace;font-size:12px;padding:6px;">Press ▶ Play to start</div>'
    log_html += '</div>'
    st.markdown(log_html, unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────
st.divider()
st.markdown(
    '<p style="text-align:center;color:#555;font-size:12px">'
    'Proactive Networking: Link-Aware Congestion Prevention System &nbsp;|&nbsp; '
    'Built with NetworkX + Streamlit</p>',
    unsafe_allow_html=True,
)

# ── Auto-play ─────────────────────────────────────────────────
if st.session_state.auto_play:
    time.sleep(delay)
    advance_stage()
    st.rerun()
