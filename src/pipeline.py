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

    chunks = retriever().search(qu.get("rewritten_query") or question, qu.get("entity_types") or None)
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
