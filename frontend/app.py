import os, streamlit as st, requests, pandas as pd
os.environ["NO_PROXY"] = "localhost,127.0.0.1"
os.environ["no_proxy"] = "localhost,127.0.0.1"
BACKEND = "http://127.0.0.1:8000"
import streamlit as st
import requests
import pandas as pd

BACKEND = st.secrets.get("backend_url", "http://localhost:8000")

st.set_page_config(page_title="PS11 Drug Repurposing (EY)", layout="wide")

st.title("🧪 Drug Discovery & Repurposing Assistant")
st.caption("MVP website — FastAPI backend + Streamlit frontend • Public APIs • Not medical advice")

with st.sidebar:
    st.header("Filters")
    min_phase = st.select_slider("Minimum trial phase", options=[0,1,2,3,4], value=0)
    exclude_boxed = st.checkbox("Exclude boxed warnings", value=False)
    route = st.selectbox("Route (placeholder)", ["any","oral","iv"], index=0)
    st.divider()
    st.caption("Backend")
    st.text(BACKEND)

disease = st.text_input("Disease / Condition", value="Idiopathic Pulmonary Fibrosis")
if st.button("Search"):
    with st.spinner("Querying APIs, linking evidence, scoring..."):
        payload = {
            "disease": disease,
            "filters": {
                "min_phase": min_phase,
                "exclude_boxed_warnings": exclude_boxed,
                "route": route,
                "include_off_label": True
            }
        }
        try:
            r = requests.post(f"{BACKEND}/search_fast", json=payload, timeout=180)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            st.error(f"Backend error: {e}")
            st.stop()

        # Table summary
        rows = []
        for item in data.get("results", []):
            rows.append({
                "Rank": item["rank"],
                "Drug": item["drug"],
                "Score": item["score"],
                "Best Phase": item["kpis"]["best_trial_phase"],
                "Papers": item["kpis"]["papers"],
                "Pos. Snippets": item["kpis"]["pos_outcome_snippets"],
                "Boxed?": "Yes" if item["safety"]["boxed_warning"] else "No"
            })
        if rows:
            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True)
        if not rows:
            st.warning("No intervention drugs found for this condition from ClinicalTrials.gov. Try a broader condition name (e.g., 'Pulmonary fibrosis' instead of 'Idiopathic Pulmonary Fibrosis').")


        # Evidence cards
        for item in data.get("results", []):
            with st.expander(f"#{item['rank']} — {item['drug']}  |  Score {item['score']}"):
                cols = st.columns([2,1])
                with cols[0]:
                    st.markdown("**Mechanism:** " + (item.get("mechanism") or "_Unknown_"))
                    st.markdown(f"**IDs:** {item.get('ids')}")
                    st.markdown(f"**Synonyms:** {', '.join(item.get('synonyms', [])[:10]) or '—'}")
                    st.markdown("**Safety:** " + ("🚫 Boxed warning" if item["safety"]["boxed_warning"] else "✅ No boxed warning in labels we fetched"))
                    for hi in item["safety"].get("highlights", []):
                        st.info(hi)
                with cols[1]:
                    st.metric("Best trial phase", item["kpis"]["best_trial_phase"])
                    st.metric("Papers", item["kpis"]["papers"])
                    st.metric("Positive cues", item["kpis"]["pos_outcome_snippets"])

                st.markdown("**Evidence:**")
                for ev in item["evidence"]:
                    link = f" ([link]({ev.get('url')}))" if ev.get("url") else ""
                    st.write(f"- *{ev['type']}* — **{ev.get('id','')}**{link}")
                    if ev.get("title"): st.write(f"  - {ev['title']}")
                    if ev.get("snippet"): st.caption(ev["snippet"])

        st.divider()
        st.caption(data.get("disclaimer", ""))

else:
    st.info("Enter a disease and click **Search** to see ranked repurposing candidates.")
