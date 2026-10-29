import streamlit as st
from src import pipeline

st.set_page_config(page_title="CivicStack", page_icon="🏢")
st.title("CivicStack")
st.caption("Grounded answers on company registration in India. Information only, not legal advice.")
st.warning("Do not enter PAN, Aadhaar or other personal data.")

version = st.sidebar.selectbox("Prompt version", ["v4", "v3", "v2", "v1"], index=0)
q = st.text_area("Ask a question", placeholder="e.g. What documents do two founders need to register a Private Limited company?")
if st.button("Ask") and q.strip():
    with st.spinner("Searching sources..."):
        out = pipeline.run(q, version, allow_clarify=True)
    st.markdown(out["answer"])
    if out["sources"]:
        with st.expander("Sources"):
            for s in out["sources"]:
                st.markdown(f"**{s['id']}** Tier {s['tier']} | {s['name']} | retrieved {s['date']} | {s['url']}")
    with st.expander("Pipeline trace"):
        st.json(out["trace"])
