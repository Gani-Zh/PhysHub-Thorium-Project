
import io
import csv
import numpy as np
import matplotlib.pyplot as plt
import streamlit as st

st.set_page_config(
    page_title="Atomic Nexus | Virtual Laboratory",
    page_icon="⚛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# STATE
# ============================================================
DEFAULTS = {
    "view": "Experiment",
    "flux": 6.0,
    "days": 365,
    "temperature": 600,
    "moderator": "Heavy Water (D₂O)",
    "coolant": "Helium",
    "scenario": "Normal Flux Scenario",
    "shutdown": False,
    "show_details": False,
    "run_counter": 0,
    "history": [],
    "compare_1": "Normal Flux Scenario",
    "compare_2": "High Flux Scenario",
    "guided_step": 1,
    "guided_hypothesis": "",
    "guided_hypothesis_reason": "",
    "guided_obs_1": "",
    "guided_obs_2": "",
    "guided_obs_3": "",
    "guided_observation_score": None,
    "guided_conclusion": "",
    "guided_conclusion_text": "",
    "guided_complete": False,
    "pending_scenario": None,
}

for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value


def reset_all():
    for key, value in DEFAULTS.items():
        st.session_state[key] = value
    st.rerun()


SCENARIO_PRESETS = {
    "Low Flux Scenario": {
        "flux": 3.0,
        "days": 500,
        "temperature": 520,
        "moderator": "Heavy Water (D₂O)",
        "coolant": "Helium",
    },
    "Normal Flux Scenario": {
        "flux": 6.0,
        "days": 365,
        "temperature": 600,
        "moderator": "Heavy Water (D₂O)",
        "coolant": "Helium",
    },
    "High Flux Scenario": {
        "flux": 8.5,
        "days": 300,
        "temperature": 680,
        "moderator": "Graphite",
        "coolant": "Molten Salt",
    },
}


def request_scenario(name: str):
    """Queue a preset and rerun before parameter widgets are instantiated."""
    st.session_state.pending_scenario = name
    st.rerun()


def apply_pending_scenario():
    """Apply queued preset before any widget using these session-state keys exists."""
    name = st.session_state.get("pending_scenario")
    if not name:
        return
    values = SCENARIO_PRESETS[name]
    for key, value in values.items():
        st.session_state[key] = value
    st.session_state.scenario = name
    st.session_state.shutdown = False
    st.session_state.view = "Experiment"
    st.session_state.pending_scenario = None


def set_view(name: str):
    st.session_state.view = name
    st.rerun()


def simulated_curves():
    # Educational / illustrative UI model only.
    days = max(float(st.session_state.days), 1.0)
    flux = max(float(st.session_state.flux), 0.1)

    x = np.logspace(0, 4, 300)
    flux_factor = flux / 6.0
    time_factor = max(days / 365.0, 0.15)

    th = 1e24 * np.exp(-np.log10(x) / (1.8 / max(flux_factor, 0.25)))
    pa = 1e19 + (1.2e21 * flux_factor) * np.exp(
        -((np.log10(x) - (1.45 + 0.08 * time_factor)) ** 2) / 0.35
    )
    u = 1e18 + (4.5e21 * min(flux_factor, 1.7)) / (
        1 + np.exp(-(np.log10(x) - (2.0 - 0.08 * flux_factor)) * 4.2)
    )

    if st.session_state.shutdown:
        pa *= 0.55
        u *= 0.70

    return x, th, pa, u


def current_summary():
    _, th, pa, u = simulated_curves()
    return {
        "scenario": st.session_state.scenario,
        "flux": float(st.session_state.flux),
        "days": int(st.session_state.days),
        "temperature": int(st.session_state.temperature),
        "moderator": st.session_state.moderator,
        "coolant": st.session_state.coolant,
        "shutdown": bool(st.session_state.shutdown),
        "final_th": float(th[-1]),
        "peak_pa": float(np.max(pa)),
        "final_u": float(u[-1]),
    }


def run_experiment():
    st.session_state.run_counter += 1
    data = current_summary()
    data["run"] = st.session_state.run_counter
    st.session_state.history.append(data)
    st.session_state.shutdown = False
    if st.session_state.view == "Guided Lab":
        st.session_state.guided_step = max(st.session_state.guided_step, 4)
    st.toast(f"Experiment #{st.session_state.run_counter} completed")


def guided_go(step: int):
    st.session_state.guided_step = step
    st.rerun()


def guided_restart():
    st.session_state.guided_step = 1
    st.session_state.guided_hypothesis = ""
    st.session_state.guided_hypothesis_reason = ""
    st.session_state.guided_obs_1 = ""
    st.session_state.guided_obs_2 = ""
    st.session_state.guided_obs_3 = ""
    st.session_state.guided_observation_score = None
    st.session_state.guided_conclusion = ""
    st.session_state.guided_conclusion_text = ""
    st.session_state.guided_complete = False
    st.rerun()


def emergency_shutdown():
    st.session_state.shutdown = True
    st.toast("Simulated emergency shutdown activated")


def history_csv():
    output = io.StringIO()
    fieldnames = [
        "run", "scenario", "flux", "days", "temperature",
        "moderator", "coolant", "shutdown", "final_th", "peak_pa", "final_u"
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for row in st.session_state.history:
        writer.writerow({key: row.get(key, "") for key in fieldnames})
    return output.getvalue().encode("utf-8")


# Apply deferred scenario changes before any widgets are instantiated.
apply_pending_scenario()

# ============================================================
# CSS
# ============================================================
st.markdown(
    """
    <style>
    #MainMenu {visibility:hidden;}
    footer {visibility:hidden;}
    header[data-testid="stHeader"] {
        background:#08111f;
        border-bottom:1px solid rgba(91,213,255,.12);
        height:58px;
    }
    [data-testid="stDecoration"] {display:none;}

    html, body, [class*="css"] {
        font-family: Inter, ui-sans-serif, system-ui, -apple-system,
        BlinkMacSystemFont, "Segoe UI", sans-serif;
    }

    .stApp {background:#07111f;color:#dfe8f7;}

    .block-container {
        max-width:1900px;
        padding-top:1rem;
        padding-left:1.2rem;
        padding-right:1.2rem;
        padding-bottom:2rem;
    }

    section[data-testid="stSidebar"] {
        background:
            radial-gradient(circle at 20% 0%, rgba(0,199,255,.10), transparent 17rem),
            linear-gradient(180deg,#06111d 0%,#071321 45%,#06111b 100%);
        border-right:1px solid rgba(85,198,239,.16);
        width:300px !important;
    }

    .side-brand {
        display:flex;gap:.75rem;align-items:center;
        padding:.55rem .25rem .75rem;
    }
    .atom-logo {
        width:40px;height:40px;border:2px solid #00cfff;border-radius:50%;
        display:flex;align-items:center;justify-content:center;
        color:#00d8ff;font-size:21px;font-weight:900;
        box-shadow:0 0 22px rgba(0,216,255,.18);
    }
    .brand-title {color:#f4f8ff;font-size:1.05rem;font-weight:800;}
    .brand-sub {color:#14cfee;font-size:.56rem;margin-top:.14rem;}

    .nav-section {
        color:#6f8aa3;font-size:.64rem;font-weight:800;
        letter-spacing:.12em;text-transform:uppercase;
        margin:1rem .2rem .35rem;
    }

    .panel {
        background:linear-gradient(180deg,#0b1d2e 0%,#091827 100%);
        border:1px solid rgba(62,183,228,.24);
        border-radius:12px;
        box-shadow:0 16px 40px rgba(0,0,0,.12);
        overflow:hidden;height:100%;
    }
    .panel-pad {padding:.78rem .9rem;}
    .panel-title {
        color:#28d8ff;font-size:.67rem;font-weight:800;
        letter-spacing:.06em;text-transform:uppercase;margin-bottom:.72rem;
    }

    .hero-row {
        display:grid;grid-template-columns:1.3fr .9fr auto;
        gap:1rem;align-items:center;margin:.2rem 0 .8rem;
    }
    .hero-title {color:#dbe6f3;font-size:1.32rem;font-weight:800;}
    .hero-sub {color:#88a1b7;font-size:.72rem;}
    .hero-note {color:#8da5ba;font-size:.69rem;line-height:1.45;}

    .live-row {
        display:grid;grid-template-columns:1.1fr .68fr .9fr;
        align-items:center;gap:.5rem;padding:.67rem 0;
        border-bottom:1px solid rgba(78,163,197,.10);font-size:.67rem;
    }
    .live-label {color:#39dbff;font-weight:700;}
    .live-value {color:#d8e7f2;}
    .spark {height:18px;width:100%;position:relative;overflow:hidden;}
    .spark:before {
        content:"";position:absolute;left:2%;right:2%;top:45%;height:1px;
        background:linear-gradient(90deg,transparent,#00cfff 18%,#00cfff 30%,transparent 32%,#00cfff 48%,#00cfff 52%,transparent 55%,#00cfff 70%,transparent);
        filter:drop-shadow(0 0 5px rgba(0,207,255,.8));
        transform:skewY(-8deg);
    }

    .flow-wrap {display:flex;align-items:stretch;gap:.42rem;}
    .flow-node {
        flex:1 1 0;min-width:0;background:#0a1c2c;
        border:1px solid rgba(65,177,217,.22);
        border-radius:9px;padding:.72rem .52rem;text-align:center;
    }
    .flow-node.good {border-color:rgba(68,220,96,.28);background:#0b2325;}
    .flow-head {color:#d7e9f4;font-size:.66rem;font-weight:800;}
    .flow-sub {color:#93a8b8;font-size:.57rem;margin-top:.12rem;}
    .flow-arrow {
        display:flex;align-items:center;justify-content:center;
        color:#1bd6ff;font-weight:900;font-size:1rem;
    }
    .flow-blob {
        width:43px;height:43px;border-radius:50%;margin:.65rem auto .15rem;
        background:radial-gradient(circle at 35% 35%,#8ef3ff 0 8%,#1aaed0 9% 25%,#08738f 26% 47%,#064b62 48% 100%);
    }

    .explain p {color:#9db0c0;font-size:.65rem;line-height:1.5;margin:.36rem 0;}
    .check {color:#57ef69;font-weight:900;margin-right:.35rem;}

    .result-grid {
        display:grid;grid-template-columns:repeat(4,1fr);gap:.45rem;
    }
    .result-cell {
        text-align:center;border-right:1px solid rgba(72,153,187,.16);
        padding:.1rem .35rem;
    }
    .result-cell:last-child {border-right:none;}
    .result-label {font-size:.52rem;color:#93a8b9;}
    .result-value {font-size:1rem;font-weight:800;color:#2bd8ff;margin-top:.34rem;}
    .result-value.green {color:#79ec55;}
    .result-value.purple {color:#a37dff;}
    .result-value.orange {color:#ffae2d;}
    .result-sub {font-size:.55rem;color:#7990a3;}

    .status-normal {
        margin-top:.55rem;color:#9db0c0;font-size:.61rem;
    }
    .status-shutdown {
        margin-top:.55rem;color:#ff8883;font-size:.61rem;font-weight:800;
    }

    .info-card {
        background:#0a2031;
        border:1px solid rgba(0,202,255,.18);
        border-radius:10px;padding:.85rem;color:#9fb4c5;
        font-size:.72rem;line-height:1.55;
    }

    .stButton>button, .stDownloadButton>button {
        width:100%;border-radius:7px;
        border:1px solid rgba(0,191,238,.35);
        background:#0a2031;color:#dcecf7;font-weight:800;
        min-height:2.25rem;font-size:.68rem;
    }
    .stButton>button:hover, .stDownloadButton>button:hover {
        border-color:#2bd8ff;color:white;background:#0b2d43;
    }
    .primary-action .stButton>button {
        background:linear-gradient(180deg,#0a8ccb,#066aa7);
        color:white;
    }
    .danger-action .stButton>button {
        border-color:rgba(255,92,92,.40);
        background:#2a1218;color:#ff6a65;
    }

    .stSlider label, .stSelectbox label {
        color:#c4d5e3 !important;font-size:.66rem !important;font-weight:700 !important;
    }
    div[data-baseweb="select"] > div {
        background:#0b2133 !important;
        border-color:rgba(70,168,205,.20) !important;
        min-height:35px !important;
    }
    div[data-baseweb="select"] span {
        color:#d5e5f1 !important;font-size:.68rem !important;
    }

    .simulated {color:#8fa4b5;font-size:.58rem;margin-top:.45rem;}
    .small-muted {color:#7c92a4;font-size:.57rem;}

    /* ---------- GUIDED LAB ---------- */
    .guide-steps {
        display:grid;
        grid-template-columns:repeat(5,1fr);
        gap:.42rem;
        margin:.2rem 0 1rem;
    }
    .guide-step {
        background:#0a1b2a;
        border:1px solid rgba(69,163,199,.18);
        border-radius:9px;
        padding:.56rem .5rem;
        color:#7891a5;
        font-size:.61rem;
        text-align:center;
        font-weight:700;
    }
    .guide-step.done {
        color:#89f275;
        border-color:rgba(92,230,87,.28);
        background:#10261f;
    }
    .guide-step.active {
        color:#dffbff;
        border-color:rgba(0,210,255,.48);
        background:#0b2a40;
        box-shadow:0 0 18px rgba(0,210,255,.06);
    }
    .learning-goal {
        background:linear-gradient(180deg,#0b2134,#091a2b);
        border:1px solid rgba(40,216,255,.26);
        border-radius:12px;
        padding:1rem 1.05rem;
        margin:.3rem 0 .8rem;
    }
    .learning-goal-title {
        color:#28d8ff;
        font-size:.68rem;
        font-weight:800;
        text-transform:uppercase;
        letter-spacing:.07em;
        margin-bottom:.45rem;
    }
    .learning-goal-text {
        color:#d4e2ec;
        font-size:.77rem;
        line-height:1.55;
    }
    .guide-question {
        background:#0a1b2b;
        border-left:3px solid #20d4ff;
        border-radius:6px;
        padding:.72rem .8rem;
        color:#bbcedd;
        font-size:.72rem;
        margin:.45rem 0;
    }
    .guide-feedback-good {
        background:#10291e;
        border:1px solid rgba(94,238,92,.28);
        border-radius:9px;
        padding:.72rem;
        color:#bdf7b4;
        font-size:.7rem;
    }
    .guide-feedback-warn {
        background:#2b2415;
        border:1px solid rgba(255,184,60,.28);
        border-radius:9px;
        padding:.72rem;
        color:#ffd78b;
        font-size:.7rem;
    }

    @media (max-width:1200px) {
        section[data-testid="stSidebar"] {width:240px !important;}
        .hero-row {grid-template-columns:1fr;}
        .result-grid {grid-template-columns:repeat(2,1fr);}
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# SIDEBAR — ALL NAVIGATION ACTIVE
# ============================================================
with st.sidebar:
    st.markdown(
        """
        <div class="side-brand">
            <div class="atom-logo">⚛</div>
            <div>
                <div class="brand-title">ATOMIC NEXUS</div>
                <div class="brand-sub">Thorium Future. Clean Energy.</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="nav-section">Dashboard</div>', unsafe_allow_html=True)
    if st.button("◫  Overview", key="nav_overview"):
        set_view("Overview")

    st.markdown('<div class="nav-section">Learn</div>', unsafe_allow_html=True)
    if st.button("◇  The Basics", key="nav_basics"):
        set_view("The Basics")
    if st.button("◉  Fuel Cycle", key="nav_cycle"):
        set_view("Fuel Cycle")
    if st.button("○  Safety", key="nav_safety"):
        set_view("Safety")
    if st.button("⌘  Technology", key="nav_tech"):
        set_view("Technology")

    st.markdown('<div class="nav-section">Virtual Lab</div>', unsafe_allow_html=True)
    if st.button("☰  Guided Lab", key="nav_guided"):
        set_view("Guided Lab")
    if st.button("⚛  Experiment", key="nav_experiment"):
        set_view("Experiment")
    if st.button("⌁  Scenarios", key="nav_scenarios"):
        set_view("Scenarios")
    if st.button("⚖  Compare", key="nav_compare"):
        set_view("Compare")
    if st.button("▣  Results History", key="nav_history"):
        set_view("Results History")

    st.markdown('<div class="nav-section">Global Data</div>', unsafe_allow_html=True)
    st.link_button("▧  IAEA PRIS ↗", "https://pris.iaea.org/PRIS/home.aspx")
    st.link_button("◎  Global Map ↗", "https://pris.iaea.org/PRIS/WorldStatistics/OperationalReactorsByCountry.aspx")

    st.markdown('<div class="nav-section">Resources</div>', unsafe_allow_html=True)
    if st.button("▤  Documents", key="nav_docs"):
        set_view("Documents")
    if st.button("▱  Glossary", key="nav_glossary"):
        set_view("Glossary")
    if st.button("▣  References", key="nav_refs"):
        set_view("References")

    st.markdown(
        """
        <div class="info-card" style="margin-top:1rem;">
            <b style="color:#67f447;">● SIMULATED TELEMETRY</b><br>
            All values in this prototype are simulated for educational visualization.
        </div>
        """,
        unsafe_allow_html=True,
    )

# ============================================================
# TOP NAV — ACTIVE
# ============================================================
top1, top2, top3, top4, top5, spacer = st.columns([1,1,1,.7,.7,4])

with top1:
    if st.button("▣  Learn", key="top_learn"):
        set_view("The Basics")
with top2:
    if st.button("⚛  Experiment", key="top_experiment"):
        set_view("Experiment")
with top3:
    if st.button("♧  Analyze", key="top_analyze"):
        set_view("Analyze")
with top4:
    if st.button("?", key="top_help"):
        st.session_state.show_details = True
        set_view("How it works")
with top5:
    if st.button("↻", key="top_reset"):
        reset_all()

st.markdown(
    """
    <div class="hero-row">
        <div>
            <div class="hero-title">Virtual Laboratory</div>
            <div class="hero-sub">Interactive simulations of the Thorium Fuel Cycle</div>
        </div>
        <div class="hero-note">Change parameters, run experiments and observe
        how the educational model responds.</div>
        <div></div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# VIEWS
# ============================================================
view = st.session_state.view

if view == "Guided Lab":
    step = int(st.session_state.guided_step)

    step_names = [
        "1 · Learning Goal",
        "2 · Hypothesis",
        "3 · Experiment",
        "4 · Observe",
        "5 · Conclusion",
    ]
    step_html = []
    for i, name in enumerate(step_names, start=1):
        cls = "guide-step"
        if i < step:
            cls += " done"
        elif i == step:
            cls += " active"
        step_html.append(f'<div class="{cls}">{name}</div>')

    st.markdown(
        '<div class="guide-steps">' + ''.join(step_html) + '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="learning-goal">
            <div class="learning-goal-title">Guided Laboratory</div>
            <div class="learning-goal-text">
                Follow the scientific learning cycle:
                <b>understand → predict → experiment → observe → conclude</b>.
                The dashboard and calculations remain the same educational simulation;
                Guided Lab only structures how a student works with them.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # STEP 1 — LEARNING GOAL
    if step == 1:
        st.subheader("Learning Goal")
        left, right = st.columns([1.45, 1], gap="small")

        with left:
            st.markdown(
                """
                <div class="panel"><div class="panel-pad">
                    <div class="panel-title">What you should understand</div>
                    <div class="guide-question">
                        By the end of this laboratory you should be able to
                        <b>identify how the three curves change over simulated time</b>
                        and explain the role of Th-232, Pa-233 and U-233
                        in the simplified educational sequence.
                    </div>
                    <p>Success criteria:</p>
                    <p>✓ Identify the decreasing curve.</p>
                    <p>✓ Identify the intermediate curve that rises and then falls.</p>
                    <p>✓ Identify the curve that grows toward a plateau.</p>
                    <p>✓ Compare your final observation with your original hypothesis.</p>
                </div></div>
                """,
                unsafe_allow_html=True,
            )

        with right:
            st.markdown(
                """
                <div class="panel"><div class="panel-pad">
                    <div class="panel-title">Before you start</div>
                    <p>This is an <b>educational simulation</b>.</p>
                    <p>Change only one main parameter at a time when investigating cause and effect.</p>
                    <p>Do not treat displayed values as operational reactor data.</p>
                </div></div>
                """,
                unsafe_allow_html=True,
            )

        if st.button("Start Guided Lab  →", key="guided_start"):
            guided_go(2)

    # STEP 2 — HYPOTHESIS
    elif step == 2:
        st.subheader("Hypothesis")
        st.markdown(
            '<div class="guide-question">Before seeing the result, predict what will happen to the U-233 curve when the simulated neutron-flux setting is increased.</div>',
            unsafe_allow_html=True,
        )

        st.radio(
            "My prediction",
            [
                "The U-233 curve will rise more strongly in the educational model.",
                "The U-233 curve will change very little.",
                "The U-233 curve will decrease.",
            ],
            key="guided_hypothesis",
        )
        st.text_area(
            "Why do you think so? (1–3 sentences)",
            key="guided_hypothesis_reason",
            placeholder="Write your reasoning before the experiment...",
            height=100,
        )

        b1, b2 = st.columns([1, 1])
        with b1:
            if st.button("←  Back", key="guided_hyp_back"):
                guided_go(1)
        with b2:
            if st.button("Save hypothesis & continue  →", key="guided_hyp_next"):
                if not st.session_state.guided_hypothesis:
                    st.warning("Choose a hypothesis first.")
                else:
                    guided_go(3)

    # STEP 3 — EXPERIMENT
    elif step == 3:
        st.subheader("Experiment")
        st.caption("Use the same controls as the free dashboard, but change one main variable deliberately.")

        control_col, graph_col = st.columns([1.05, 2.15], gap="small")

        with control_col:
            st.markdown(
                '<div class="panel"><div class="panel-pad"><div class="panel-title">Guided Settings</div>',
                unsafe_allow_html=True,
            )
            st.slider(
                "Neutron Flux (relative scale)",
                1.0,
                10.0,
                step=0.1,
                key="flux",
            )
            st.slider(
                "Simulation Time (days)",
                30,
                1000,
                step=5,
                key="days",
            )
            st.markdown(
                '<div class="small-muted">Recommended first run: keep time fixed and change only the relative flux setting.</div>',
                unsafe_allow_html=True,
            )
            st.markdown('</div></div>', unsafe_allow_html=True)

            if st.button("▶  Run Guided Experiment", key="guided_run"):
                run_experiment()
                st.session_state.guided_step = 4
                st.rerun()

            if st.button("←  Back to Hypothesis", key="guided_exp_back"):
                guided_go(2)

        with graph_col:
            x, th, pa, u = simulated_curves()
            fig, ax = plt.subplots(figsize=(8.2, 4.0))
            ax.plot(x, th, linewidth=2, label="Th-232")
            ax.plot(x, pa, linewidth=2, label="Pa-233")
            ax.plot(x, u, linewidth=2, label="U-233")
            ax.set_xscale("log")
            ax.set_yscale("log")
            ax.set_xlabel("Time (days)")
            ax.set_ylabel("Normalized educational model")
            ax.grid(True, alpha=.18)
            ax.legend(loc="upper center", ncol=3, frameon=False)
            ax.set_facecolor("#0b1d2e")
            fig.patch.set_facecolor("#0b1d2e")
            ax.tick_params(colors="#9fb2c1", labelsize=8)
            ax.xaxis.label.set_color("#a8bac7")
            ax.yaxis.label.set_color("#a8bac7")
            for spine in ax.spines.values():
                spine.set_color("#23435a")
            for t in ax.get_legend().get_texts():
                t.set_color("#d4e3ed")
            st.pyplot(fig, width="stretch")

    # STEP 4 — OBSERVATION QUESTIONS
    elif step == 4:
        st.subheader("Observation Questions")
        st.caption("Answer from the graph you observed. These questions test graph interpretation, not memorization.")

        x, th, pa, u = simulated_curves()
        fig, ax = plt.subplots(figsize=(8.4, 3.8))
        ax.plot(x, th, linewidth=2, label="Th-232")
        ax.plot(x, pa, linewidth=2, label="Pa-233")
        ax.plot(x, u, linewidth=2, label="U-233")
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlabel("Time (days)")
        ax.set_ylabel("Normalized educational model")
        ax.grid(True, alpha=.18)
        ax.legend(loc="upper center", ncol=3, frameon=False)
        ax.set_facecolor("#0b1d2e")
        fig.patch.set_facecolor("#0b1d2e")
        ax.tick_params(colors="#9fb2c1", labelsize=8)
        ax.xaxis.label.set_color("#a8bac7")
        ax.yaxis.label.set_color("#a8bac7")
        for spine in ax.spines.values():
            spine.set_color("#23435a")
        for t in ax.get_legend().get_texts():
            t.set_color("#d4e3ed")
        st.pyplot(fig, width="stretch")

        q1, q2, q3 = st.columns(3, gap="small")
        with q1:
            st.radio(
                "1. Which curve decreases continuously?",
                ["Choose...", "Th-232", "Pa-233", "U-233"],
                key="guided_obs_1",
            )
        with q2:
            st.radio(
                "2. Which curve rises and then falls?",
                ["Choose...", "Th-232", "Pa-233", "U-233"],
                key="guided_obs_2",
            )
        with q3:
            st.radio(
                "3. Which curve grows toward a plateau?",
                ["Choose...", "Th-232", "Pa-233", "U-233"],
                key="guided_obs_3",
            )

        c1, c2 = st.columns([1, 1])
        with c1:
            if st.button("Check observations", key="guided_check_obs"):
                answers = [
                    st.session_state.guided_obs_1 == "Th-232",
                    st.session_state.guided_obs_2 == "Pa-233",
                    st.session_state.guided_obs_3 == "U-233",
                ]
                st.session_state.guided_observation_score = sum(answers)
        with c2:
            if st.button("Continue to conclusion  →", key="guided_obs_next"):
                if st.session_state.guided_observation_score is None:
                    st.warning("Check your observations first.")
                else:
                    guided_go(5)

        if st.session_state.guided_observation_score is not None:
            score = st.session_state.guided_observation_score
            if score == 3:
                st.markdown(
                    '<div class="guide-feedback-good">3/3 — All observations match the displayed curves.</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f'<div class="guide-feedback-warn">{score}/3 — Recheck the graph and compare the shape of each curve before continuing.</div>',
                    unsafe_allow_html=True,
                )

    # STEP 5 — CONCLUSION
    elif step == 5:
        st.subheader("Conclusion")
        st.markdown(
            '<div class="guide-question">Compare the observed result with the hypothesis you wrote before the experiment.</div>',
            unsafe_allow_html=True,
        )

        st.write("**Your hypothesis:**")
        st.write(st.session_state.guided_hypothesis or "No hypothesis saved.")
        if st.session_state.guided_hypothesis_reason:
            st.caption(st.session_state.guided_hypothesis_reason)

        st.radio(
            "Was your hypothesis supported by the displayed educational model?",
            [
                "Yes — the result supported my prediction.",
                "Partly — some observations matched, but I would revise my explanation.",
                "No — the result did not support my prediction.",
            ],
            key="guided_conclusion",
        )

        st.text_area(
            "Write your conclusion",
            key="guided_conclusion_text",
            placeholder="Example structure: I predicted... I observed... Therefore...",
            height=120,
        )

        if st.button("Complete Guided Lab", key="guided_finish"):
            if not st.session_state.guided_conclusion or not st.session_state.guided_conclusion_text.strip():
                st.warning("Select a conclusion and write a short final statement.")
            else:
                st.session_state.guided_complete = True

        if st.session_state.guided_complete:
            st.success("Guided Lab completed.")
            st.markdown(
                f"""
                <div class="panel"><div class="panel-pad">
                    <div class="panel-title">Learning Summary</div>
                    <p><b>Observation score:</b> {st.session_state.guided_observation_score}/3</p>
                    <p><b>Scientific process completed:</b> goal → hypothesis → experiment → observation → conclusion.</p>
                    <p><b>Next step:</b> repeat the experiment in Free Experiment mode and change one variable at a time.</p>
                </div></div>
                """,
                unsafe_allow_html=True,
            )
            a, b = st.columns(2)
            with a:
                if st.button("Open Free Experiment", key="guided_to_free"):
                    set_view("Experiment")
            with b:
                if st.button("Restart Guided Lab", key="guided_restart"):
                    guided_restart()

elif view == "Experiment":
    settings_col, graph_col, live_col = st.columns([1.12, 2.0, 1.35], gap="small")

    with settings_col:
        st.markdown('<div class="panel"><div class="panel-pad"><div class="panel-title">Experiment Settings</div>', unsafe_allow_html=True)

        st.slider("Neutron Flux (relative scale)", 1.0, 10.0, step=0.1, key="flux")
        st.slider("Simulation Time (days)", 30, 1000, step=5, key="days")
        st.slider("Temperature (°C)", 300, 1000, step=10, key="temperature")

        st.selectbox(
            "Moderator Type",
            ["Heavy Water (D₂O)", "Graphite", "Light Water"],
            key="moderator",
        )
        st.selectbox(
            "Coolant Type",
            ["Helium", "Molten Salt", "Water"],
            key="coolant",
        )

        st.markdown('<div class="primary-action">', unsafe_allow_html=True)
        if st.button("▶  Run Experiment", key="run_experiment"):
            run_experiment()
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="danger-action">', unsafe_allow_html=True)
        if st.button("⏻  Emergency Shutdown", key="shutdown_btn"):
            emergency_shutdown()
        st.markdown('</div>', unsafe_allow_html=True)

        if st.session_state.shutdown:
            st.markdown(
                '<div class="status-shutdown">● Simulated shutdown active</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div class="status-normal">● Reactor Status: <b style="color:#65ef4f;">Normal Simulation</b></div>',
                unsafe_allow_html=True,
            )

        st.markdown('</div></div>', unsafe_allow_html=True)

    with graph_col:
        st.markdown('<div class="panel"><div class="panel-pad"><div class="panel-title">Nuclide Concentrations</div>', unsafe_allow_html=True)

        x, th, pa, u = simulated_curves()
        fig, ax = plt.subplots(figsize=(8.0, 4.0))
        ax.plot(x, th, linewidth=2, label="Th-232")
        ax.plot(x, pa, linewidth=2, label="Pa-233")
        ax.plot(x, u, linewidth=2, label="U-233")
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlabel("Time (days)")
        ax.set_ylabel("Normalized educational model")
        ax.grid(True, alpha=.18)
        ax.legend(loc="upper center", ncol=3, frameon=False)
        ax.set_facecolor("#0b1d2e")
        fig.patch.set_facecolor("#0b1d2e")
        ax.tick_params(colors="#9fb2c1", labelsize=8)
        ax.xaxis.label.set_color("#a8bac7")
        ax.yaxis.label.set_color("#a8bac7")
        for spine in ax.spines.values():
            spine.set_color("#23435a")
        for text in ax.get_legend().get_texts():
            text.set_color("#d4e3ed")
        st.pyplot(fig, width="stretch")
        st.markdown('</div></div>', unsafe_allow_html=True)

    with live_col:
        power = 0 if st.session_state.shutdown else 850
        temp = max(320, st.session_state.temperature + (0 if not st.session_state.shutdown else -140))
        flux_value = 0 if st.session_state.shutdown else st.session_state.flux

        st.markdown(
            f"""
            <div class="panel"><div class="panel-pad">
            <div class="panel-title">Live Parameters</div>
            <div class="live-row"><div class="live-label">Reactor Power</div><div class="live-value">{power} MW(th)</div><div class="spark"></div></div>
            <div class="live-row"><div class="live-label">Core Temperature</div><div class="live-value">{temp} °C</div><div class="spark"></div></div>
            <div class="live-row"><div class="live-label">Neutron Flux</div><div class="live-value">{flux_value:.2f} rel.</div><div class="spark"></div></div>
            <div class="live-row"><div class="live-label">Mode</div><div class="live-value">{"STOPPED" if st.session_state.shutdown else "SIMULATED"}</div><div class="spark"></div></div>
            <div class="live-row"><div class="live-label">Run Count</div><div class="live-value">{st.session_state.run_counter}</div><div class="spark"></div></div>
            <div class="simulated">ⓘ All data are simulated</div>
            </div></div>
            """,
            unsafe_allow_html=True,
        )

    flow_col, explain_col = st.columns([3.1, 1.25], gap="small")

    with flow_col:
        st.markdown(
            """
            <div class="panel"><div class="panel-pad">
            <div class="panel-title">Fuel Cycle Flow Diagram</div>
            <div class="flow-wrap">
                <div class="flow-node">
                    <div class="flow-head">Th-232</div>
                    <div class="flow-sub">Thorium</div>
                    <div class="flow-blob"></div>
                </div>
                <div class="flow-arrow">→</div>
                <div class="flow-node">
                    <div class="flow-head">Pa-233</div>
                    <div class="flow-sub">Protactinium</div>
                    <div class="flow-blob"></div>
                </div>
                <div class="flow-arrow">→</div>
                <div class="flow-node good">
                    <div class="flow-head">U-233</div>
                    <div class="flow-sub">Uranium</div>
                    <div class="flow-blob"></div>
                </div>
                <div class="flow-arrow">→</div>
                <div class="flow-node">
                    <div class="flow-head">Energy</div>
                    <div class="flow-sub">Educational model</div>
                    <div style="font-size:2rem;margin:.8rem auto .15rem;">⚡</div>
                </div>
                <div class="flow-arrow">→</div>
                <div class="flow-node">
                    <div class="flow-head">Review</div>
                    <div class="flow-sub">Interpretation</div>
                    <div style="font-size:2rem;margin:.8rem auto .15rem;">◫</div>
                </div>
            </div>
            </div></div>
            """,
            unsafe_allow_html=True,
        )

    with explain_col:
        st.markdown(
            """
            <div class="panel"><div class="panel-pad explain">
            <div class="panel-title">Explanation Engine</div>
            <p>The educational model visualizes a simplified sequence:</p>
            <p><span class="check">✓</span>Th-232 decreases over simulated time.</p>
            <p><span class="check">✓</span>Pa-233 appears as an intermediate curve.</p>
            <p><span class="check">✓</span>U-233 grows in the illustrative model.</p>
            </div></div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("💡  Show Details", key="show_details_btn"):
            st.session_state.show_details = not st.session_state.show_details
        if st.session_state.show_details:
            st.info(
                "This panel explains only what the simplified educational curves show. "
                "It is not an operational reactor model."
            )

    preset_col, result_col, compare_col = st.columns([1.12, 1.75, 1.45], gap="small")

    with preset_col:
        st.markdown('<div class="panel"><div class="panel-pad"><div class="panel-title">Preset Scenarios</div><div class="small-muted">Start with a predefined scenario</div>', unsafe_allow_html=True)
        if st.button("Low Flux Scenario", key="preset_low"):
            request_scenario("Low Flux Scenario")
        if st.button("Normal Flux Scenario", key="preset_normal"):
            request_scenario("Normal Flux Scenario")
        if st.button("High Flux Scenario", key="preset_high"):
            request_scenario("High Flux Scenario")
        st.markdown('</div></div>', unsafe_allow_html=True)

    with result_col:
        summary = current_summary()
        st.markdown(
            f"""
            <div class="panel"><div class="panel-pad">
            <div class="panel-title">Results Summary</div>
            <div class="result-grid">
                <div class="result-cell">
                    <div class="result-label">Final Th-232</div>
                    <div class="result-value green">{summary["final_th"]:.2e}</div>
                    <div class="result-sub">illustrative</div>
                </div>
                <div class="result-cell">
                    <div class="result-label">Peak Pa-233</div>
                    <div class="result-value">{summary["peak_pa"]:.2e}</div>
                    <div class="result-sub">illustrative</div>
                </div>
                <div class="result-cell">
                    <div class="result-label">Final U-233</div>
                    <div class="result-value purple">{summary["final_u"]:.2e}</div>
                    <div class="result-sub">illustrative</div>
                </div>
                <div class="result-cell">
                    <div class="result-label">Runs</div>
                    <div class="result-value orange">{st.session_state.run_counter}</div>
                    <div class="result-sub">session</div>
                </div>
            </div>
            </div></div>
            """,
            unsafe_allow_html=True,
        )

        st.download_button(
            "⇩  Download Results",
            data=history_csv(),
            file_name="atomic_nexus_results.csv",
            mime="text/csv",
            key="download_results",
        )

    with compare_col:
        st.markdown('<div class="panel"><div class="panel-pad"><div class="panel-title">Compare Experiments</div><div class="small-muted">Select two scenarios to compare</div>', unsafe_allow_html=True)
        st.selectbox(
            "Experiment 1",
            ["Normal Flux Scenario", "Low Flux Scenario", "High Flux Scenario"],
            key="compare_1",
        )
        st.selectbox(
            "Experiment 2",
            ["High Flux Scenario", "Normal Flux Scenario", "Low Flux Scenario"],
            key="compare_2",
        )
        if st.button("⚖  Compare", key="compare_btn"):
            st.session_state.view = "Compare"
            st.rerun()
        st.markdown('</div></div>', unsafe_allow_html=True)

elif view == "Scenarios":
    st.subheader("Preset Scenarios")
    st.caption("Choose a scenario. The button applies settings and returns to Experiment.")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown('<div class="panel"><div class="panel-pad"><div class="panel-title">Low Flux Scenario</div><p>Lower illustrative flux and longer observation.</p></div></div>', unsafe_allow_html=True)
        if st.button("Apply Low Flux", key="scenario_low"):
            request_scenario("Low Flux Scenario")
    with c2:
        st.markdown('<div class="panel"><div class="panel-pad"><div class="panel-title">Normal Flux Scenario</div><p>Reference educational preset.</p></div></div>', unsafe_allow_html=True)
        if st.button("Apply Normal Flux", key="scenario_normal"):
            request_scenario("Normal Flux Scenario")
    with c3:
        st.markdown('<div class="panel"><div class="panel-pad"><div class="panel-title">High Flux Scenario</div><p>Higher illustrative flux and shorter observation.</p></div></div>', unsafe_allow_html=True)
        if st.button("Apply High Flux", key="scenario_high"):
            request_scenario("High Flux Scenario")

elif view == "Compare":
    st.subheader("Compare Experiments")
    st.caption("Scenario comparison uses the same educational UI model.")

    scenarios = {
        "Low Flux Scenario": (3.0, 500),
        "Normal Flux Scenario": (6.0, 365),
        "High Flux Scenario": (8.5, 300),
    }

    a = st.session_state.compare_1
    b = st.session_state.compare_2
    flux_a, days_a = scenarios[a]
    flux_b, days_b = scenarios[b]

    c1, c2 = st.columns(2)
    with c1:
        st.metric("Scenario A", a)
        st.metric("Relative flux", flux_a)
        st.metric("Days", days_a)
    with c2:
        st.metric("Scenario B", b)
        st.metric("Relative flux", flux_b)
        st.metric("Days", days_b)

    st.info(
        "This comparison is for educational visualization only. "
        "It does not represent engineering or operational performance."
    )

elif view == "Results History":
    st.subheader("Results History")
    if not st.session_state.history:
        st.info("No completed experiments in this session yet.")
    else:
        st.dataframe(st.session_state.history, width="stretch")
        st.download_button(
            "Download session CSV",
            data=history_csv(),
            file_name="atomic_nexus_history.csv",
            mime="text/csv",
            key="history_download",
        )

elif view == "Analyze":
    st.subheader("Analyze")
    summary = current_summary()
    a, b, c = st.columns(3)
    a.metric("Final Th-232", f'{summary["final_th"]:.2e}')
    b.metric("Peak Pa-233", f'{summary["peak_pa"]:.2e}')
    c.metric("Final U-233", f'{summary["final_u"]:.2e}')
    st.info(
        "The Analyze view converts the current visual result into a structured "
        "student-facing interpretation."
    )

elif view == "Overview":
    st.subheader("Overview")
    st.markdown(
        """
        <div class="info-card">
        <b>Atomic Nexus Virtual Laboratory</b><br><br>
        Learn → Experiment → Analyze is the core workflow.
        The main landing page remains the visual benchmark.
        </div>
        """,
        unsafe_allow_html=True,
    )

elif view == "The Basics":
    st.subheader("The Basics")
    st.write(
        "This section introduces the purpose of the virtual laboratory, "
        "the simplified learning model, and how to interpret the interface."
    )

elif view == "Fuel Cycle":
    st.subheader("Fuel Cycle")
    st.write(
        "The learning sequence visualizes Th-232 → Pa-233 → U-233 "
        "as a simplified educational progression."
    )

elif view == "Safety":
    st.subheader("Safety")
    st.info(
        "All controls and telemetry in this prototype are simulated. "
        "The interface is designed for educational use."
    )

elif view == "Technology":
    st.subheader("Technology")
    st.write(
        "The application uses Streamlit for interaction and Python for "
        "educational visualization."
    )

elif view == "Documents":
    st.subheader("Documents")
    st.write("Project documentation area.")

elif view == "Glossary":
    st.subheader("Glossary")
    st.markdown(
        """
        **Th-232** — thorium-232  
        **Pa-233** — protactinium-233  
        **U-233** — uranium-233  
        **Simulation** — a simplified computational representation used for learning
        """
    )

elif view == "References":
    st.subheader("References")
    st.link_button("IAEA PRIS", "https://pris.iaea.org/PRIS/home.aspx")
    st.caption("Additional verified educational references can be added here.")

elif view == "How it works":
    st.subheader("How it works")
    st.markdown(
        """
        1. Choose a preset or change the educational parameters.
        2. Run an experiment.
        3. Observe the curves and simulated telemetry.
        4. Open Analyze to interpret the result.
        5. Save/download the session results.
        """
    )

st.markdown(
    """
    <div style="margin-top:.8rem;color:#516a7e;font-size:.56rem;text-align:right;">
    ATOMIC NEXUS · Virtual Laboratory v3 Guided FIXED · Main page remains the visual benchmark
    </div>
    """,
    unsafe_allow_html=True,
)
