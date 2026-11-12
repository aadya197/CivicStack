"""Compare prompt versions on the test set. Saves after every row, so a quota error never loses work.

Examples
  python3 -m eval.run_eval --versions v1 v4 --limit 4          # generate answers only
  python3 -m eval.run_eval --versions v1 v4 --judge            # generate, then judge with the LLM
  python3 -m eval.run_eval --judge-only                        # judge rows that have no scores yet
  python3 -m eval.run_eval --ids Q12 Q14 Q15 --versions v1 v4  # only some questions

Re-running with the same --out resumes: rows already done are skipped.
Ground truth must be checked by the team. LLM judge scores are a screening aid: spot-check by hand."""
import argparse
import re
import sys
from pathlib import Path

import pandas as pd

from src import config, llm, pipeline

SCORES = ["correctness", "faithfulness", "citation_accuracy", "completeness", "behaviour"]

ap = argparse.ArgumentParser()
ap.add_argument("--versions", nargs="+", default=["v1", "v2", "v3", "v4"])
ap.add_argument("--limit", type=int, default=None)
ap.add_argument("--ids", nargs="+", default=None)
ap.add_argument("--judge", action="store_true")
ap.add_argument("--judge-only", action="store_true")
ap.add_argument("--out", default=str(config.ROOT / "eval" / "results" / "run_main.csv"))
args = ap.parse_args()

out_path = Path(args.out)
out_path.parent.mkdir(parents=True, exist_ok=True)
tests = pd.read_csv(config.ROOT / "eval" / "test_set.csv")
if args.ids:
    tests = tests[tests["id"].isin(args.ids)]
if args.limit:
    tests = tests.head(args.limit)
judge_t = (config.ROOT / "eval" / "judge_prompt.txt").read_text(encoding="utf-8")

try:
    rows = pd.read_csv(out_path).to_dict("records") if out_path.exists() else []
except pd.errors.EmptyDataError:   # an empty file left behind by an earlier run that stopped at once
    rows = []
done = {(r["id"], r["version"]) for r in rows}


def save():
    if rows:
        pd.DataFrame(rows).to_csv(out_path, index=False)


def is_quota(e: Exception) -> bool:
    s = str(e)
    return "429" in s or "RESOURCE_EXHAUSTED" in s or "quota" in s.lower()


def stop_for_quota():
    save()
    print(f"\nAPI quota reached. Progress saved to {out_path} ({len(rows)} rows).")
    print("Run the same command again later (or switch model/billing); finished rows are skipped.")
    sys.exit(0)


# ---- phase 1: generate answers ----
if not args.judge_only:
    for _, r in tests.iterrows():
        for v in args.versions:
            if (r["id"], v) in done:
                continue
            try:
                out = pipeline.run(r["question"], v)
            except Exception as e:
                if is_quota(e):
                    stop_for_quota()
                print(f"{r['id']} {v} ERROR: {e}")
                continue
            rows.append({"id": r["id"], "category": r["category"], "version": v, "question": r["question"],
                         "answer": out["answer"], "n_sources": len(out["sources"]), "context": out["context"]})
            done.add((r["id"], v))
            save()
            print(r["id"], v, "answered")

# ---- phase 2: judge rows without scores ----
if args.judge or args.judge_only:
    meta = tests.set_index("id")
    for row in rows:
        if row["id"] not in meta.index or pd.notna(row.get("correctness")):
            continue
        t = meta.loc[row["id"]]
        ctx = row.get("context")
        kw = {"category": t["category"], "expected_behavior": t["expected_behavior"], "question": t["question"],
              "ground_truth": t["ground_truth"], "context": ctx if isinstance(ctx, str) and ctx else "(none)",
              "answer": row["answer"]}
        p = re.sub(r"\{(\w+)\}", lambda m: str(kw.get(m.group(1), m.group(0))), judge_t)
        try:
            row.update(llm.json_call(p))
        except Exception as e:
            if is_quota(e):
                stop_for_quota()
            row["note"] = f"judge_error: {e}"
        save()
        print(row["id"], row["version"], "judged")

save()
res = pd.DataFrame(rows)
cols = [c for c in SCORES if c in res and res[c].notna().any()]
if cols:
    print(res.groupby("version")[cols].mean().round(2))
print(f"Saved {len(rows)} rows to {out_path}")
