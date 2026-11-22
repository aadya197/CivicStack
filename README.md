# CivicStack: grounded RAG assistant for company registration in India

Prompt Engineering mini-project (Bennett University). Answers questions on entity types, documents, fees, compliances, timelines and common pending issues, using only retrieved sources with citations. **Information only, not legal, tax or investment advice.**

## Architecture
See `docs/architecture.md`. Pipeline: query understanding -> hybrid retrieval (dense + BM25, tier-weighted) -> grounded cited answer -> claim verifier.

## Setup
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # add GEMINI_API_KEY
```

## Build the knowledge base
1. Add exact URLs or downloaded files to `data/sources.yaml` and set `enabled: true`.
2. Add real observations to `data/feedback/feedback.csv` (Tier 3).
3. `python -m src.ingest`

## Run
```bash
python -m src.pipeline "What documents are needed for a Private Limited company?" v4
streamlit run app.py
```

## Evaluate
Fill `ground_truth` in `eval/test_set.csv` from Tier 1 sources, then:
```bash
python -m eval.run_eval --versions v1 v2 v3 v4 --judge
```
Spot-check judge scores by hand. Log each prompt change in `docs/PROMPT_LOG.md`.

## Prompt versions
V1 baseline (no RAG) | V2 basic RAG | V3 cited + refusal + tier rules | V4 query understanding + verifier chain.

## Responsible use
No personal data in prompts or test cases. Sources are cited, not republished. Fees and rules change: every answer shows source dates. Tier 3 content is labelled as reported experience.

## Known limitations (v0)
Word-window chunking (heading-aware chunking is a planned experiment); English only; scraped pages may be incomplete; LLM-judge is a screening aid.
# CivicStack

## Prototype
https://civicstack-skjzxntkvqpfepsay56gn7.streamlit.app

## Team
Aadya Gupta (S24CSEU1220), Rajan Ahuja (S24CSEU1218), Garvit Narang (S24CSEU1174)

## Folder guide
- `prompts/v1`, `v2`, `v3`: older prompt versions; `prompts/final`: the three final prompts
- `src/` and `app.py`: the running code (`code/` holds a reference copy of the main modules)
- `test-data/`: test questions with ground truth and saved scores
- `docs/`: diagrams, prompt log and the Milestone 2 PDF
- `CHANGELOG.md`: dated list of changes
