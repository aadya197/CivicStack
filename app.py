"""CivicStack demo app. Run locally: streamlit run app.py
Tabs: Ask (live), Compare V1 vs V4 (live), Test results (no API calls), About."""
import json
import os

import pandas as pd
import streamlit as st

from src import config

st.set_page_config(page_title="CivicStack", page_icon="🏢", layout="wide")
MAX_QUERIES = int(os.getenv("MAX_QUERIES_PER_SESSION", "6"))


@st.cache_resource(show_spinner="Preparing the knowledge base (first start only)...")
def ensure_index() -> str:
    """Build the search index on first start if it is missing (needed on a fresh deployment)."""
    chunks_path = config.PROCESSED_DIR / "chunks.jsonl"
    chroma_dir = config.INDEX_DIR / "chroma"
    if chunks_path.exists() and chroma_dir.exists():
        return "ready"
    from src import ingest
    if chunks_path.exists():
        rows = [json.loads(line) for line in open(chunks_path, encoding="utf-8")]
    else:
        rows = ingest.build_chunks()
    ingest.build_index(rows)
    return "built"


def pipeline():
    from src import pipeline as p
    return p


def friendly_error(e: Exception) -> str:
    s = str(e)
    if "429" in s or "RESOURCE_EXHAUSTED" in s or "quota" in s.lower():
        return "The shared API quota is used up for now. The 'Test results' tab shows saved answers and needs no API calls."
    return f"Something went wrong: {s[:300]}"


def show_answer(out: dict):
    st.markdown(out["answer"])
    if out.get("sources"):
        with st.expander("Sources used"):
            for s in out["sources"]:
                st.markdown(f"**{s['id']}** - Tier {s['tier']} - {s['name']} - retrieved {s['date']}")
    with st.expander("Pipeline trace"):
        st.json(out.get("trace", {}))


def quota_left() -> bool:
    return st.session_state.get("queries", 0) < MAX_QUERIES


st.title("CivicStack")
st.caption("Source-grounded answers on company registration in India. Information only, not legal, tax or investment advice.")
st.warning("Do not enter PAN, Aadhaar or other personal data.")

tab_ask, tab_cmp, tab_res, tab_about = st.tabs(["Ask", "Compare V1 vs V4", "Test results", "About"])

with tab_ask:
    q = st.text_area("Your question", key="q_ask", placeholder="e.g. How long can a reserved company name be extended and at what fee?")
    if st.button("Ask", key="btn_ask") and q.strip():
        if not quota_left():
            st.info(f"Session limit of {MAX_QUERIES} live questions reached. See the 'Test results' tab.")
        else:
            try:
                ensure_index()
                with st.spinner("Searching sources and checking the answer..."):
                    out = pipeline().run(q, "v4", allow_clarify=True)
                st.session_state["queries"] = st.session_state.get("queries", 0) + 1
                show_answer(out)
            except Exception as e:
                st.error(friendly_error(e))
    st.caption(f"Live questions used this session: {st.session_state.get('queries', 0)} of {MAX_QUERIES}")

with tab_cmp:
    st.write("Same question, no retrieval (V1) versus the full pipeline (V4). Uses four API calls.")
    q2 = st.text_input("Question", key="q_cmp", value="Within how many days must the Central Processing Centre Registrar decide a filing?")
    if st.button("Compare", key="btn_cmp") and q2.strip():
        if st.session_state.get("queries", 0) + 2 > MAX_QUERIES:
            st.info("Not enough live questions left in this session. See the 'Test results' tab.")
        else:
            try:
                ensure_index()
                c1, c2 = st.columns(2)
                with st.spinner("Running both versions..."):
                    o1 = pipeline().run(q2, "v1")
                    o4 = pipeline().run(q2, "v4", allow_clarify=True)
                st.session_state["queries"] = st.session_state.get("queries", 0) + 2
                with c1:
                    st.subheader("V1: model only")
                    show_answer(o1)
                with c2:
                    st.subheader("V4: CivicStack")
                    show_answer(o4)
            except Exception as e:
                st.error(friendly_error(e))

with tab_res:
    res_dir = config.ROOT / "eval" / "results"
    ans_path, sc_path = res_dir / "run_final_v43.csv", res_dir / "scores_all_versions.csv"
    if not (ans_path.exists() and sc_path.exists()):
        st.info("Saved evaluation files were not found in eval/results/.")
    else:
        ans, sc = pd.read_csv(ans_path), pd.read_csv(sc_path)
        final = sc[sc.version.isin(["v4.3", "v4.4"])].sort_values("version").drop_duplicates("id", keep="last").set_index("id")
        v1 = sc[sc.version == "v1"].set_index("id")
        tbl = pd.DataFrame({"V1 score /10": v1.total_of_10, "Final score /10": final.total_of_10}).dropna().astype(int)
        tbl["Final pass"] = (final.total_of_10 >= 7) & (final.behaviour == 2)
        m1, m2, m3 = st.columns(3)
        m1.metric("V1 total", f"{int(tbl['V1 score /10'].sum())} / {10 * len(tbl)}")
        m2.metric("Final total", f"{int(tbl['Final score /10'].sum())} / {10 * len(tbl)}")
        m3.metric("Tests passed (final)", f"{int(tbl['Final pass'].sum())} / {len(tbl)}")
        st.dataframe(tbl, use_container_width=True)
        st.caption("Scores 0-10 against a ground truth taken from the Tier 1 texts; a test passes at 7 or more with correct behaviour. One run, 16 questions.")
        for qid in sorted(tbl.index):
            sub = ans[ans.id == qid]
            if sub.empty:
                continue
            with st.expander(f"{qid}: {sub.iloc[0]['question']}"):
                cc1, cc2 = st.columns(2)
                for col, ver, title in [(cc1, "v1", "V1 (no retrieval)"), (cc2, "v4", "V4 (final)")]:
                    r = sub[sub.version == ver]
                    with col:
                        st.markdown(f"**{title}**")
                        st.markdown(r.iloc[0]["answer"] if not r.empty else "(not run)")

with tab_about:
    st.markdown(
        "**CivicStack** answers questions about registering a company in India from a curated knowledge base: "
        "Acts, Rules and Gazette notifications (Tier 1), practitioner guides (Tier 2) and, when available, real feedback (Tier 3). "
        "A three-prompt chain (query understanding, grounded answer, verifier) with hybrid retrieval, source tiers, refusals and guards. "
        "Answers show their sources and retrieval dates. Rules and fees change, so verify on the MCA portal or with a CA/CS.")
