import os
import requests
import pandas as pd
import streamlit as st
try:
    import plotly.express as px
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except Exception:
    HAS_PLOTLY = False

# Ensure localhost calls bypass proxies on some Windows setups
os.environ["NO_PROXY"] = "localhost,127.0.0.1"
os.environ["no_proxy"] = "localhost,127.0.0.1"

BACKEND = st.secrets.get("backend_url", "http://localhost:8000")

st.set_page_config(page_title="PS11 Drug Repurposing (EY)", layout="wide")

st.title("🧪 Drug Discovery & Repurposing Assistant")
st.caption("Research prototype — Not medical advice")

# Top-level navigation
treat_tab, explorer_tab, compare_tab = st.tabs(["Treatments", "Explorer", "Compare"])

# Minimal modern look & feel
st.markdown(
    """
    <style>
      /* NeoBio Intelligence theme */
      .stApp { background: #FFFFFF; color:#1A1A1A; }
      header, .st-emotion-cache-18ni7ap { background:#003366 !important; }
      /* Cards */
      .result-card {
        border: 1px solid #E0E5EC; border-radius: 12px; padding: 16px; margin-bottom: 14px; background: #FFFFFF;
        box-shadow: 0 2px 8px rgba(46,58,70,0.10);
      }
      /* Pills & badges */
      .pill { display:inline-block; padding: 2px 10px; border-radius: 999px; background:#00B8D922; color:#003366; font-size:12px; margin-left:6px }
      .pill.warn { background:#FFC10722; color:#FFC107 }
      .pill.positive { background:#27AE6022; color:#27AE60 }
      .pill.alert { background:#FF6F6122; color:#FF6F61 }
      /* Sections */
      .muted { color:#4A4A4A; }
      .section-title { font-weight:600; font-size:14px; margin: 8px 0 4px; color:#2E3A46; }
      /* Metrics */
      [data-testid="stMetricValue"] { font-size: 16px !important; color:#003366 !important; }
      [data-testid="stMetricLabel"] { font-size: 12px !important; color:#4A4A4A !important; }
      /* Buttons */
      .stButton>button { background:#00B8D9; color:#FFFFFF; border:none; border-radius:8px; }
      .stButton>button:hover { background:#0099b8; }
      /* Sidebar */
      section[data-testid="stSidebar"] { background:#E0E5EC }
      /* Inputs */
      .stTextInput>div>div>input, .stNumberInput input, .stSelectbox div[data-baseweb="select"]>div { background:#FFFFFF; color:#1A1A1A }
    </style>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Filters")
    colp1, colp2 = st.columns(2)
    with colp1:
        min_phase = st.selectbox("Min phase", ["Any", "Phase 1", "Phase 2", "Phase 3"], index=0)
    with colp2:
        min_year = st.number_input("Min year", min_value=0, max_value=2100, value=0, step=1)
    st.caption("Quick filters")
    c1, c2, c3 = st.columns(3)
    if c1.button("Phase 3"):
        min_phase = "Phase 3"
    if c2.button("Recent ≥2018"):
        min_year = 2018
    if c3.button("Reset"):
        min_phase, min_year = "Any", 0
    st.divider()

with treat_tab:
    disease = st.text_input("Disease / Condition", value="Idiopathic Pulmonary Fibrosis", placeholder="e.g., breast cancer, kidney failure, migraine")

@st.cache_data(show_spinner=False, ttl=600)
def fetch_treatments(backend_url: str, condition: str, min_phase: str, min_year: int, max_records: int = 30):
    phase_map = {
        "Any": "any",
        "Phase 1": "phase 1",
        "Phase 2": "phase 2",
        "Phase 3": "phase 3",
    }
    params = {
        "condition": condition,
        "max_records": max_records,
        "min_phase": phase_map.get(min_phase, "any"),
        "min_year": int(min_year or 0),
    }
    r = requests.get(f"{backend_url}/api/treat", params=params, timeout=120)
    r.raise_for_status()
    return r.json()

with treat_tab:
    search = st.button("Search")
if 'search' in locals() and search:
    with st.spinner("Querying APIs, linking evidence, scoring..."):
        try:
            data = fetch_treatments(BACKEND, disease, min_phase, min_year)
        except Exception as e:
            st.error(f"Backend error: {e}")
            st.stop()

        # Table summary
        items = data.get("treatments", [])
        if not items:
            st.warning("No candidate medicines found. Try a broader condition name.")

        # Responsive card grid (3 columns on wide screens)
        cols_per_row = 3
        rows = [items[i:i+cols_per_row] for i in range(0, len(items), cols_per_row)]
        for row in rows:
            cols = st.columns(cols_per_row)
            for col, item in zip(cols, row):
                with col:
                    with st.container():
                        st.markdown(f"<div class='result-card'>", unsafe_allow_html=True)
                        title = item.get("medicine", "Unknown")
                        st.markdown(f"### {title} <span class='pill'>Confidence {item.get('confidence',0):.2f}</span>", unsafe_allow_html=True)
                        m = item.get("metrics") or {}
                        c1, c2, c3 = st.columns(3)
                        with c1:
                            st.metric("Trials", m.get("trials", 0))
                        with c2:
                            st.metric("Publications", m.get("publications", 0))
                        with c3:
                            st.metric("Top phase", m.get("topPhase", ""))
                        if item.get("summary"):
                            st.markdown(f"<div class='muted'>{item.get('summary')}</div>", unsafe_allow_html=True)

                        # Actions
                        a1, a2 = st.columns(2)
                        with a1:
                            with st.popover("Sources"):
                                srcs = item.get("sources", []) or []
                                if not srcs:
                                    st.caption("No sources provided")
                                for s in srcs:
                                    st.write(f"- {s}")
                        with a2:
                            if st.button("Copy summary", key=f"copy-{title}"):
                                st.session_state[f"copied-{title}"] = item.get("summary") or ""
                                st.success("Summary copied (select and copy)")
                                st.code(item.get("summary") or "")

                        st.markdown("</div>", unsafe_allow_html=True)

        # Persist last medicines for Compare tab
        try:
            st.session_state["last_meds"] = [it.get("medicine") for it in items if it.get("medicine")]
        except Exception:
            pass

        # Optional deep-dive list view with download
        with st.expander("Details list"):
            table_rows = []
            for item in items:
                table_rows.append({
                    "Medicine": item.get("medicine"),
                    "Confidence": item.get("confidence"),
                    "Trials": (item.get("metrics") or {}).get("trials"),
                    "Publications": (item.get("metrics") or {}).get("publications"),
                    "Top Phase": (item.get("metrics") or {}).get("topPhase"),
                })
            if table_rows:
                df = pd.DataFrame(table_rows)
                st.dataframe(df, use_container_width=True)
                st.download_button("Download CSV", df.to_csv(index=False).encode("utf-8"), file_name="treatments.csv", mime="text/csv")


with explorer_tab:
    # Controls at the very top of Explorer tab
    colx1, colx2, colx3 = st.columns([2,1,1])
    with colx1:
        explorer_condition = st.text_input("Condition for exploration", value=(locals().get('disease') or "migraine"), placeholder="e.g., migraine")
    with colx2:
        explorer_max = st.slider("Max items", min_value=6, max_value=30, value=12, step=3)
    with colx3:
        trigger_explorer = st.button("Explore", use_container_width=True)

@st.cache_data(show_spinner=False, ttl=600)
def fetch_explorer(backend_url: str, condition: str, max_records: int):
    r = requests.get(f"{backend_url}/api/explorer", params={"condition": condition, "max_records": max_records}, timeout=120)
    r.raise_for_status()
    return r.json()

if 'trigger_explorer' in locals() and trigger_explorer:
    with st.spinner("Exploring molecules, markets and patents..."):
        try:
            ex = fetch_explorer(BACKEND, explorer_condition, int(explorer_max))
        except Exception as e:
            st.error(f"Backend error: {e}")
            st.stop()

    items = ex.get("items", [])
    if not items:
        st.warning("No explorer items found for this condition.")
    else:
        with explorer_tab:
            # Top bar chart by confidence
            try:
                chart_df = pd.DataFrame({
                    "Medicine": [i.get("medicine") for i in items],
                    "Confidence": [i.get("confidence", 0) for i in items],
                }).sort_values("Confidence", ascending=False)
                st.bar_chart(chart_df.set_index("Medicine"))
            except Exception:
                pass

            # Helper to convert dictionaries into 0–100 scores
            def score_0_100(d: dict, kind: str) -> int:
                if not isinstance(d, dict):
                    return 0
                # direct score in 0..1 or 0..100
                if isinstance(d.get("score"), (int, float)):
                    v = d.get("score")
                    return int(v*100) if 0 <= v <= 1 else int(max(0, min(100, v)))
                # heuristic mappings
                txt = str((d.get("need") or d.get("risk") or d.get("pathway") or d.get("note") or "")).lower()
                if "high" in txt and kind == "market":
                    return 85
                if "medium" in txt and kind == "market":
                    return 60
                if "low" in txt and kind == "market":
                    return 35
                if "low" in txt and kind == "patent":  # low risk is good
                    return 85
                if "medium" in txt and kind == "patent":
                    return 60
                if "high" in txt and kind == "patent":
                    return 25
                if "fast" in txt or "priority" in txt and kind == "reg":
                    return 80
                if "unassessed" in txt or "demo" in txt:
                    return 0
                return 0

            # Grid of cards
            cols_per_row = 3
            rows = [items[i:i+cols_per_row] for i in range(0, len(items), cols_per_row)]
            for row in rows:
                cols = st.columns(cols_per_row)
                for col, it in zip(cols, row):
                    with col:
                        with st.container():
                            st.markdown(f"<div class='result-card'>", unsafe_allow_html=True)
                            st.markdown(f"### {it.get('medicine','Unknown')} <span class='pill'>Conf {it.get('confidence',0):.2f}</span>", unsafe_allow_html=True)
                            mkt, pat, reg = it.get("market", {}), it.get("patent", {}), it.get("regulatory", {})

                            # Metrics row
                            try:
                                mc1, mc2, mc3 = st.columns(3)
                                with mc1:
                                    st.metric("Trials", (it.get("metrics") or {}).get("trials", 0))
                                with mc2:
                                    st.metric("Pubs", (it.get("metrics") or {}).get("publications", 0))
                                with mc3:
                                    st.metric("Top", (it.get("metrics") or {}).get("topPhase", ""))
                            except Exception:
                                pass

                            # Numeric summaries out of 100 for easy interpretation
                            s_market = score_0_100(mkt, "market")
                            s_patent = score_0_100(pat, "patent")
                            s_reg = score_0_100(reg, "reg")

                            # Fallback heuristics when backend did not return scores
                            mtr = it.get("metrics") or {}
                            trials_cnt = int(mtr.get("trials") or 0)
                            pubs_cnt = int(mtr.get("publications") or 0)
                            phase = (mtr.get("topPhase") or "").lower()
                            phase_boost = {"phase 3": 25, "phase 2": 15, "phase 1": 8}.get(phase, 0)
                            conf = float(it.get("confidence") or 0.0)

                            if s_market == 0:
                                s_market = int(min(100, max(5, conf*100 + trials_cnt*8 + pubs_cnt*5 + phase_boost + 5)))
                            if s_patent == 0:
                                s_patent = int(min(100, max(5, 70 - pubs_cnt*6 - (15 if phase == "phase 3" else 0) + conf*10)))
                            if s_reg == 0:
                                s_reg = int(min(100, max(5, 40 + phase_boost + min(30, trials_cnt*6) + conf*20)))

                            r1, r2, r3 = st.columns(3)
                            with r1:
                                st.metric("Market", f"{s_market}/100")
                            with r2:
                                st.metric("Patent", f"{s_patent}/100")
                            with r3:
                                st.metric("Regulatory", f"{s_reg}/100")

                            st.markdown("</div>", unsafe_allow_html=True)

        st.divider()
        # no disclaimer in new API

@st.cache_data(show_spinner=False, ttl=600)
def fetch_drug_info_cached(backend_url: str, name: str):
    r = requests.get(f"{backend_url}/api/drug/{name}", timeout=60)
    r.raise_for_status()
    return r.json()

@st.cache_data(show_spinner=False, ttl=600)
def fetch_counts_cached(backend_url: str, name: str):
    res = {"trials": 0, "publications": 0}
    try:
        t = requests.get(f"{backend_url}/api/trials", params={"drug": name, "max_records": 30}, timeout=60)
        t.raise_for_status(); res["trials"] = len(t.json().get("results", []))
    except Exception:
        pass
    try:
        l = requests.get(f"{backend_url}/api/literature", params={"drug": name, "max_records": 30}, timeout=60)
        l.raise_for_status(); res["publications"] = len(l.json().get("results", []))
    except Exception:
        pass
    return res

with compare_tab:
    st.subheader("Drug Comparison")
    opts = st.session_state.get("last_meds", [])
    cc1, cc2 = st.columns(2)
    with cc1:
        drug_a = st.selectbox("Drug A", options=opts or [""], index=0 if opts else 0, key="cmp_a")
        drug_a = st.text_input("Or type Drug A", value=drug_a or "Metformin", key="cmp_a_text")
    with cc2:
        drug_b = st.selectbox("Drug B", options=opts or [""], index=1 if (opts and len(opts)>1) else 0, key="cmp_b")
        drug_b = st.text_input("Or type Drug B", value=drug_b or "Sildenafil", key="cmp_b_text")

    run_compare = st.button("Compare", use_container_width=True)
    if run_compare:
        def build_rationale(name: str, counts: dict, info: dict) -> str:
            trials = int(counts.get("trials") or 0)
            pubs = int(counts.get("publications") or 0)
            boxed = bool((info.get("safety", {}) or {}).get("boxed_warning"))
            mech = info.get("mechanism")
            parts = []
            if trials > 0:
                parts.append(f"evidence from {trials} clinical trial{'s' if trials!=1 else ''}")
            if pubs > 0:
                parts.append(f"{pubs} publication{'s' if pubs!=1 else ''} suggesting activity")
            if mech:
                parts.append("defined mechanism of action")
            if not boxed:
                parts.append("no boxed safety warning in labels we checked")
            if not parts:
                return f"Use of {name} is theoretically plausible based on limited signals; further validation is needed."
            return f"{name} may be considered due to " + ", ".join(parts) + "."

        cols = st.columns(2)
        compare_results = []
        for col, name in zip(cols, [drug_a, drug_b]):
            with col:
                with st.spinner(f"Fetching data for {name}..."):
                    try:
                        info = fetch_drug_info_cached(BACKEND, name)
                        counts = fetch_counts_cached(BACKEND, name)
                    except Exception as e:
                        st.error(f"{name}: {e}")
                        continue
                compare_results.append({"name": name, "info": info, "counts": counts})
                st.markdown(f"### {info.get('name', name)}")
                mcol1, mcol2, mcol3 = st.columns(3)
                with mcol1:
                    st.metric("Trials", counts.get("trials", 0))
                with mcol2:
                    st.metric("Publications", counts.get("publications", 0))
                with mcol3:
                    st.metric("Boxed warning", "Yes" if (info.get("safety", {}).get("boxed_warning")) else "No")
                st.caption("Mechanism")
                st.write(info.get("mechanism") or "—")
                if info.get("targets"):
                    st.caption("Targets")
                    st.write(", ".join([str(x) for x in info.get("targets")]))
                if (info.get("safety", {}).get("highlights")):
                    st.caption("Safety highlights")
                    for h in info.get("safety", {}).get("highlights", [])[:3]:
                        st.info(h)
                st.caption("Why this drug?")
                st.write(build_rationale(name, counts, info))

        # Head-to-head theoretical comparison
        if len(compare_results) == 2:
            a, b = compare_results
            def score(entry: dict) -> int:
                c = entry["counts"]; i = entry["info"]
                s = 0
                s += int(c.get("trials", 0)) * 3
                s += int(c.get("publications", 0)) * 2
                s += 5 if not (i.get("safety", {}) or {}).get("boxed_warning") else -5
                s += 2 if i.get("mechanism") else 0
                return s
            sa, sb = score(a), score(b)
            st.subheader("Theoretical comparison")
            if sa > sb:
                st.success(f"{a['name']} edges {b['name']} based on combined evidence (score {sa} vs {sb}).")
            elif sb > sa:
                st.success(f"{b['name']} edges {a['name']} based on combined evidence (score {sb} vs {sa}).")
            else:
                st.info(f"Both drugs appear comparable in current signals (score {sa}).")

            # Interactive graphs
            st.subheader("Interactive graphs")
            if HAS_PLOTLY:
                # 1) Bar chart of trials vs publications
                bar_df = pd.DataFrame([
                    {"Drug": a["name"], "Trials": a["counts"].get("trials", 0), "Publications": a["counts"].get("publications", 0)},
                    {"Drug": b["name"], "Trials": b["counts"].get("trials", 0), "Publications": b["counts"].get("publications", 0)},
                ])
                bar_df = bar_df.melt(id_vars=["Drug"], var_name="Metric", value_name="Count")
                st.plotly_chart(px.bar(bar_df, x="Drug", y="Count", color="Metric", barmode="group", height=350), use_container_width=True)

                # 2) Radar (spider) for normalized view
                def norm(v):
                    return max(0, min(1, float(v)))
                ax = ["Trials", "Publications", "Safety", "Mechanism"]
                a_vals = [norm(a["counts"].get("trials",0)/10), norm(a["counts"].get("publications",0)/10), 1.0 if not (a["info"].get("safety",{}) or {}).get("boxed_warning") else 0.3, 1.0 if a["info"].get("mechanism") else 0.2]
                b_vals = [norm(b["counts"].get("trials",0)/10), norm(b["counts"].get("publications",0)/10), 1.0 if not (b["info"].get("safety",{}) or {}).get("boxed_warning") else 0.3, 1.0 if b["info"].get("mechanism") else 0.2]
                fig = go.Figure()
                fig.add_trace(go.Scatterpolar(r=a_vals + [a_vals[0]], theta=ax + [ax[0]], fill='toself', name=a['name']))
                fig.add_trace(go.Scatterpolar(r=b_vals + [b_vals[0]], theta=ax + [ax[0]], fill='toself', name=b['name']))
                fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0,1])), showlegend=True, height=400)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Plotly is not installed. Showing basic chart. Run: pip install plotly==5.24.1")
                bar_df = pd.DataFrame([
                    {"Drug": a["name"], "Trials": a["counts"].get("trials", 0), "Publications": a["counts"].get("publications", 0)},
                    {"Drug": b["name"], "Trials": b["counts"].get("trials", 0), "Publications": b["counts"].get("publications", 0)},
                ])
                st.bar_chart(bar_df.set_index("Drug"))

if 'search' not in locals() or not search:
    st.info("Enter a disease and click **Search** to see ranked repurposing candidates.")
