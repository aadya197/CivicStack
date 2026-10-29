"""Compare prompt versions on the test set.
Usage: python -m eval.run_eval --versions v1 v2 v3 v4 [--limit 5] [--judge]
Ground truth must be written by the team from Tier 1 sources. LLM judge scores are a
screening aid: spot-check them by hand and report human scores in the final report."""
import argparse
import datetime as dt
import re

import pandas as pd

from src import config, llm, pipeline

ap = argparse.ArgumentParser()
ap.add_argument("--versions", nargs="+", default=["v1", "v2", "v3", "v4"])
ap.add_argument("--limit", type=int, default=None)
ap.add_argument("--judge", action="store_true")
args = ap.parse_args()

df = pd.read_csv(config.ROOT / "eval" / "test_set.csv")
if args.limit:
    df = df.head(args.limit)
judge_t = (config.ROOT / "eval" / "judge_prompt.txt").read_text(encoding="utf-8")
rows = []
for _, r in df.iterrows():
    for v in args.versions:
        out = pipeline.run(r["question"], v)
        row = {"id": r["id"], "category": r["category"], "version": v, "question": r["question"],
               "answer": out["answer"], "n_sources": len(out["sources"])}
        if args.judge:
            kw = {"category": r["category"], "expected_behavior": r["expected_behavior"],
                  "question": r["question"], "ground_truth": r["ground_truth"],
                  "context": out["context"] or "(none)", "answer": out["answer"]}
            p = re.sub(r"\{(\w+)\}", lambda m: str(kw.get(m.group(1), m.group(0))), judge_t)
            try:
                row.update(llm.json_call(p))
            except Exception as e:
                row["note"] = f"judge_error: {e}"
        rows.append(row)
        print(r["id"], v, "done")

res = pd.DataFrame(rows)
ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
(config.ROOT / "eval" / "results").mkdir(exist_ok=True)
res.to_csv(config.ROOT / "eval" / "results" / f"run_{ts}.csv", index=False)
if args.judge:
    cols = [c for c in ["correctness", "faithfulness", "citation_accuracy", "completeness", "behaviour"] if c in res]
    print(res.groupby("version")[cols].mean().round(2))
