"""CivicStack demo app. Run locally: streamlit run app.py
Tabs: Ask (live), Compare V1 vs V4 (live), Test results (no API calls), About.
Layout and styling live in civic_ui.py; the pipeline in src/ is untouched."""
import hashlib
import os

import pandas as pd
import streamlit as st
import yaml

import civic_ui as ui
from src import config

st.set_page_config(page_title="CivicStack", page_icon="🏢", layout="wide", initial_sidebar_state="collapsed")
MAX_QUERIES = int(os.getenv("MAX_QUERIES_PER_SESSION", "6"))
REPO_URL = "https://github.com/aadya197/CivicStack"


def html(markup: str) -> None:
    st.markdown(markup, unsafe_allow_html=True)


# ----------------------------------------------------------------------------- backend glue (unchanged behaviour)
@st.cache_resource(show_spinner="Preparing the knowledge base (first start only)...")
def ensure_index() -> str:
    """Build the search index if it is missing, or if data/sources.yaml changed since it was built."""
    sig = hashlib.md5(config.SOURCES_YAML.read_bytes()).hexdigest()
    chunks_path = config.PROCESSED_DIR / "chunks.jsonl"
    chroma_dir = config.INDEX_DIR / "chroma"
    stamp = config.INDEX_DIR / "sources.sig"
    if chunks_path.exists() and chroma_dir.exists() and stamp.exists() and stamp.read_text().strip() == sig:
        return "ready"
    from src import ingest
    rows = ingest.build_chunks()
    ingest.build_index(rows)
    config.INDEX_DIR.mkdir(parents=True, exist_ok=True)
    stamp.write_text(sig)
    return "built"


def pipeline():
    from src import pipeline as p
    return p


def friendly_error(e: Exception) -> str:
    s = str(e)
    if "429" in s or "RESOURCE_EXHAUSTED" in s or "quota" in s.lower():
        return "The shared API quota is used up for now. The 'Test results' tab shows saved answers and needs no API calls."
    return f"Something went wrong: {s[:300]}"


def quota_left() -> bool:
    return st.session_state.get("queries", 0) < MAX_QUERIES


# ----------------------------------------------------------------------------- read-only data for display
@st.cache_data(show_spinner=False)
def kb_summary() -> dict:
    try:
        rows = yaml.safe_load(config.SOURCES_YAML.read_text(encoding="utf-8")) or []
    except Exception:
        return {"counts": {}, "total": 0}
    counts = ui.kb_counts(rows)
    return {"counts": counts, "total": sum(counts.values())}


@st.cache_data(show_spinner=False)
def eval_data():
    """Saved evaluation results (no API calls). Returns (answers, scores_table, categories) or None."""
    res_dir = config.ROOT / "eval" / "results"
    ans_path, sc_path = res_dir / "run_final_v43.csv", res_dir / "scores_all_versions.csv"
    if not (ans_path.exists() and sc_path.exists()):
        return None
    ans, sc = pd.read_csv(ans_path), pd.read_csv(sc_path)
    final = sc[sc.version.isin(["v4.3", "v4.4"])].sort_values("version").drop_duplicates("id", keep="last").set_index("id")
    v1 = sc[sc.version == "v1"].set_index("id")
    tbl = pd.DataFrame({"V1 score /10": v1.total_of_10, "Final score /10": final.total_of_10}).dropna().astype(int)
    tbl["Final pass"] = (final.total_of_10 >= 7) & (final.behaviour == 2)
    cats = {}
    try:
        ts = pd.read_csv(config.ROOT / "eval" / "test_set.csv")
        cats = dict(zip(ts["id"], ts["category"]))
    except Exception:
        pass
    return ans, tbl, cats


# ----------------------------------------------------------------------------- answer rendering
def show_answer(out: dict, title: str = "Research brief") -> None:
    notice = ui.notice_for(out)
    if notice:
        html(notice)
    else:
        rep = ui.report_html(out, title)
        if rep:
            html(rep)
        else:
            with st.container(border=True):
                st.markdown(out["answer"])
    src = ui.sources_html(out)
    if src:
        html(src)
    with st.expander("How this answer was produced"):
        chips = ui.trace_chips_html(out.get("trace", {}))
        if chips:
            html(chips)
        html(ui.json_html(out.get("trace", {})))


# ----------------------------------------------------------------------------- page chrome
dark = st.session_state.get("dark_mode", True)
html(ui.theme_css(dark))
top_l, top_r = st.columns([6, 1.3])
with top_l:
    html(ui.topbar_html())
with top_r:
    st.toggle("Dark mode", value=True, key="dark_mode")

kb = kb_summary()
ev = eval_data()
has_result = bool(st.session_state.get("ask_out"))

tab_ask, tab_cmp, tab_res, tab_about = st.tabs(["💬 Ask", "⚖️ Compare V1 vs V4", "📊 Test results", "ℹ️ About"])

# ----------------------------------------------------------------------------- Ask
with tab_ask:
    def use_example(text: str) -> None:
        st.session_state["q_ask"] = text

    html(ui.hero_html(compact=has_result))
    q = st.text_area("Your question", key="q_ask", height=110, label_visibility="collapsed",
                     placeholder="Ask anything, e.g. How long can a reserved company name be extended and at what fee?")
    c_btn, c_quota = st.columns([1, 2])
    with c_btn:
        go = st.button("Ask CivicStack  →", key="btn_ask", type="primary")
    with c_quota:
        quota_slot = st.empty()

    html(ui.label_html("Try an example"))
    ex_cols = st.columns(2)
    for i, ex in enumerate(ui.EXAMPLES):
        ex_cols[i % 2].button(ex, key=f"ex_{i}", on_click=use_example, args=(ex,))

    loading_slot = st.empty()
    ran = False
    if go:
        if not q.strip():
            html(ui.alert_html("info", "Type a question first", "Or pick one of the examples above."))
        elif not quota_left():
            html(ui.alert_html("warn", "Session limit reached", f"You have used {MAX_QUERIES} live questions. The 'Test results' tab shows saved answers."))
        else:
            try:
                ensure_index()
                loading_slot.markdown(ui.loading_html(), unsafe_allow_html=True)
                out = pipeline().run(q, "v4", allow_clarify=True)
                loading_slot.empty()
                st.session_state["queries"] = st.session_state.get("queries", 0) + 1
                st.session_state["ask_out"] = {"q": q, "out": out}
                ran = True
            except Exception as e:
                loading_slot.empty()
                st.session_state.pop("ask_out", None)
                html(ui.alert_html("err", "Could not get an answer", friendly_error(e)))
    if ran:
        st.rerun()

    last = st.session_state.get("ask_out")
    if last:
        html(ui.label_html("Your question"))
        html(f'<div style="font-weight:600;font-size:1.12rem;margin-bottom:6px;color:var(--ink)">{ui.esc(last["q"])}</div>')
        show_answer(last["out"])
    else:
        stats = []
        if kb["total"]:
            stats.append(("Sources indexed", str(kb["total"])))
        if ev is not None:
            _, tbl, _ = ev
            stats += [("Test questions", str(len(tbl))),
                      ("Score vs baseline", f"{int(tbl['Final score /10'].sum())} vs {int(tbl['V1 score /10'].sum())}"),
                      ("Tests passed", f"{int(tbl['Final pass'].sum())} / {len(tbl)}")]
        if stats:
            html(ui.stats_html(stats))
        html(ui.features_html())

    quota_slot.markdown(ui.quota_html(st.session_state.get("queries", 0), MAX_QUERIES), unsafe_allow_html=True)

# ----------------------------------------------------------------------------- Compare
with tab_cmp:
    st.markdown("### Compare V1 and V4")
    st.caption("Same question, no retrieval (V1) versus the full pipeline (V4). Uses four API calls.")
    q2 = st.text_input("Question", key="q_cmp", label_visibility="collapsed",
                       value="Within how many days must the Central Processing Centre Registrar decide a filing?")
    go2 = st.button("Run comparison  →", key="btn_cmp", type="primary")
    loading_slot2 = st.empty()
    if go2 and q2.strip():
        if st.session_state.get("queries", 0) + 2 > MAX_QUERIES:
            html(ui.alert_html("warn", "Not enough live questions left", "See the 'Test results' tab for saved answers."))
        else:
            try:
                ensure_index()
                loading_slot2.markdown(ui.loading_html(("Running V1: model only", "Retrieving sources for V4", "Drafting a cited answer", "Verifying every claim")),
                                       unsafe_allow_html=True)
                o1 = pipeline().run(q2, "v1")
                o4 = pipeline().run(q2, "v4", allow_clarify=True)
                loading_slot2.empty()
                st.session_state["queries"] = st.session_state.get("queries", 0) + 2
                st.session_state["cmp_out"] = {"q": q2, "o1": o1, "o4": o4}
            except Exception as e:
                loading_slot2.empty()
                st.session_state.pop("cmp_out", None)
                html(ui.alert_html("err", "Could not run the comparison", friendly_error(e)))

    last = st.session_state.get("cmp_out")
    if last:
        html(ui.label_html("Question"))
        html(f'<div style="font-weight:600;font-size:1.1rem;margin-bottom:8px;color:var(--ink)">{ui.esc(last["q"])}</div>')
        html(ui.compare_strip_html(last["o1"], last["o4"]))
        c1, c2 = st.columns(2)
        with c1:
            html(ui.vs_tag_html("v1"))
            show_answer(last["o1"], "V1 answer")
        with c2:
            html(ui.vs_tag_html("v4"))
            show_answer(last["o4"], "V4 answer")
    html(ui.quota_html(st.session_state.get("queries", 0), MAX_QUERIES))

# ----------------------------------------------------------------------------- Test results
with tab_res:
    st.markdown("### Evaluation results")
    if ev is None:
        html(ui.alert_html("info", "No saved results", "Saved evaluation files were not found in eval/results/."))
    else:
        ans, tbl, cats = ev
        ans_q = ans.drop_duplicates("id").set_index("id")["question"].to_dict()
        rows = [{"id": qid, "question": ans_q.get(qid, ""), "category": cats.get(qid, ""),
                 "v1": int(r["V1 score /10"]), "final": int(r["Final score /10"]), "passed": bool(r["Final pass"])}
                for qid, r in tbl.sort_index().iterrows()]
        html(ui.results_dashboard_html(rows))
        st.caption("Scores 0-10 against a ground truth taken from the Tier 1 texts; a test passes at 7 or more with correct behaviour. One run, 16 questions.")

        st.markdown("### Saved answers")
        for qid in sorted(tbl.index):
            sub = ans[ans.id == qid]
            if sub.empty:
                continue
            mark = "✓" if bool(tbl.loc[qid, "Final pass"]) else "✗"
            label = f"{mark}  {qid} · {sub.iloc[0]['question']}  ({tbl.loc[qid, 'V1 score /10']} → {tbl.loc[qid, 'Final score /10']})"
            with st.expander(label):
                cc1, cc2 = st.columns(2)
                for col, ver in [(cc1, "v1"), (cc2, "v4")]:
                    r = sub[sub.version == ver]
                    with col:
                        html(ui.vs_tag_html(ver))
                        st.markdown(r.iloc[0]["answer"] if not r.empty else "(not run)")

# ----------------------------------------------------------------------------- About
with tab_about:
    st.markdown("### About CivicStack")
    st.write("CivicStack answers questions about registering a company in India from a curated knowledge base: "
             "Acts, Rules and Gazette notifications (Tier 1), practitioner guides (Tier 2) and, when available, real feedback (Tier 3). "
             "Answers show their sources and retrieval dates. Rules and fees change, so verify on the MCA portal or with a CA/CS.")
    stats = [("Sources indexed", str(kb["total"]))] if kb["total"] else []
    if ev is not None:
        _, tbl, _ = ev
        stats += [("Baseline score (V1)", f"{int(tbl['V1 score /10'].sum())} / {10 * len(tbl)}"),
                  ("Final score", f"{int(tbl['Final score /10'].sum())} / {10 * len(tbl)}"),
                  ("Tests passed", f"{int(tbl['Final pass'].sum())} / {len(tbl)}")]
    if stats:
        html(ui.stats_html(stats))

    st.markdown("### How it works")
    html(ui.steps_html())
    st.markdown("### Source tiers")
    html(ui.tiers_html(kb["counts"] or None))
    st.markdown("### Limits and the team")
    html('<div class="cs-grid">'
         + ui.card_html("Limits and responsible use",
                        "Information only, not legal, tax or investment advice. The assistant refuses off-topic and advice-seeking questions, "
                        "says when its sources do not cover something, and does not list common rejection reasons unless reported experience exists. "
                        "Do not enter personal data such as PAN or Aadhaar. Check the official MCA portal or ask a CA/CS before filing.", "lock")
         + ui.card_html("Project",
                        "Prompt Engineering mini project (SCSE4041), Bennett University.<br>Team: Aadya Gupta, Rajan Ahuja, Garvit Narang. Faculty: Indrajeet Gupta.<br>"
                        f'<a href="{ui.esc(REPO_URL)}" target="_blank" rel="noopener noreferrer">Source code on GitHub ↗</a>', "stack")
         + "</div>")

html('<div class="cs-foot">CivicStack · Source-grounded answers on company registration in India · Information only, not legal, tax or investment advice. '
     'Do not enter PAN, Aadhaar or other personal data.</div>')
