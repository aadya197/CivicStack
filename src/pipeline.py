"""Prompt versions V1-V4. Run: python -m src.pipeline "your question" v4"""
import datetime as dt
import re
import sys

from src import config, llm

PROMPTS = config.ROOT / "src" / "prompts"
DISCLAIMER = ("_Information only, not legal, tax or investment advice. Rules and fees change; "
              "verify on the official MCA portal or with a CA/CS before filing._")
REFUSAL = ("I can only give general information about registering and running a company in India. "
           "I can't give investment, share-market, tax-saving or legal advice. "
           "For that, please consult a qualified professional.")

_retriever = None


def retriever():
    global _retriever
    if _retriever is None:
        from src.retriever import Retriever
        _retriever = Retriever()
    return _retriever


def prompt(name: str, **kw) -> str:
    text = (PROMPTS / name).read_text(encoding="utf-8")
    return re.sub(r"\{(\w+)\}", lambda m: str(kw.get(m.group(1), m.group(0))), text)


def format_context(chunks):
    blocks = []
    for i, c in enumerate(chunks, 1):
        head = f"[S{i}] Tier {c['tier']} | {c['source_name']} | retrieved {c.get('date_retrieved', '')} | {c.get('url', '')}"
        blocks.append(f"{head}\n{c['text']}")
    return "\n\n".join(blocks)


def sources_list(chunks):
    return [{"id": f"S{i}", "tier": c["tier"], "name": c["source_name"],
             "url": c.get("url", ""), "date": c.get("date_retrieved", "")}
            for i, c in enumerate(chunks, 1)]


EXPAND = [
    (r"non[- ]?profit|\bngo\b|charit|community group|social welfare",
     "section 8 company promoting commerce art science sports education research social welfare religion charity no dividend"),
    (r"annual filing|annual compliance|annual return|yearly filing",
     "annual general meeting section 96 annual return section 92 financial statements section 137 DIR-3 KYC"),
]


def normalize_query(q: str) -> str:
    """Map everyday terms to the statute's wording so retrieval finds the right sections."""
    q = re.sub(r"\bprivate\s+limited(\s+company)?\b", "private company", q, flags=re.I)
    q = re.sub(r"\bpvt\.?\s*ltd\.?\b", "private company", q, flags=re.I)
    q = re.sub(r"\bpublic\s+limited(\s+company)?\b", "public company", q, flags=re.I)
    # Add the statute's own vocabulary so retrieval finds the right sections.
    for pat, extra in EXPAND:
        if re.search(pat, q, flags=re.I):
            q += " " + extra
    return q


def run(question: str, version: str = "v4", allow_clarify: bool = False) -> dict:
    trace = {"version": version}
    system = "You are CivicStack, an information assistant for company registration in India."

    if version == "v1":
        ans = llm.complete(prompt("v1_baseline.txt", question=question))
        return {"answer": ans, "sources": [], "context": "", "trace": trace}

    if version in ("v2", "v3"):
        chunks = retriever().search(question)
        ctx = format_context(chunks)
        tmpl = "v2_basic_rag.txt" if version == "v2" else "v3_cited.txt"
        ans = llm.complete(prompt(tmpl, question=question, context=ctx), system=system)
        return {"answer": ans, "sources": sources_list(chunks), "context": ctx, "trace": trace}

    # ---- V4: understand -> (clarify) -> retrieve -> answer -> verify ----
    try:
        qu = llm.json_call(prompt("query_understanding.txt", question=question))
    except Exception as e:
        qu = {"intent": "other_in_scope", "entity_types": [], "missing_info": [], "rewritten_query": question}
        trace["qu_error"] = str(e)
    trace["query_understanding"] = qu

    if qu.get("intent") == "out_of_scope":
        return {"answer": REFUSAL, "sources": [], "context": "", "trace": trace}

    if allow_clarify and qu.get("intent") == "compare_entities" and qu.get("missing_info"):
        need = ", ".join(m.replace("_", " ") for m in qu["missing_info"])
        return {"answer": f"To give a useful comparison, could you tell me: {need}?",
                "sources": [], "context": "", "trace": trace}

    primary = retriever().search(normalize_query(qu.get("rewritten_query") or question), qu.get("entity_types") or None)
    extra = retriever().search(normalize_query(question), None)
    seen, chunks = set(), []
    from itertools import zip_longest
    for a, b in zip_longest(primary, extra):
        for c in (a, b):
            if c and c["id"] not in seen:
                seen.add(c["id"])
                chunks.append(c)
    chunks = chunks[:8]
    if qu.get("intent") == "common_issues":
        chunks = [c for c in chunks if int(c["tier"]) == 3]
        if not chunks:
            msg = ("I could not find reported experience about delays or rejections in the available sources, "
                   "so I will not list common reasons as if they were established. "
                   "Please check the MCA portal guidance or ask a CA/CS who files incorporations regularly.")
            return {"answer": msg + "\n\n" + DISCLAIMER, "sources": [], "context": "", "trace": trace}
    ctx = format_context(chunks)
    draft = llm.complete(prompt("answer_v4.txt", question=question, context=ctx,
                                today=dt.date.today().isoformat()), system=system)
    trace["draft"] = draft
    try:
        ver = llm.json_call(prompt("verifier.txt", context=ctx, answer=draft), max_tokens=4096)
        trace["verifier_claims"] = ver.get("claims", [])
        final = ver.get("corrected_answer") or draft
    except Exception as e:
        trace["verifier_error"] = str(e)
        final = draft
    return {"answer": final + "\n\n" + DISCLAIMER, "sources": sources_list(chunks),
            "context": ctx, "trace": trace}


if __name__ == "__main__":
    q = sys.argv[1]
    v = sys.argv[2] if len(sys.argv) > 2 else "v4"
    out = run(q, v)
    print(out["answer"])
    for s in out["sources"]:
        print(s)
