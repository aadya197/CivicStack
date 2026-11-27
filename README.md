# CivicStack

A source-grounded RAG assistant for company registration in India. It answers questions on entity types, documents, fees, compliances and deadlines from official Acts, Rules and Gazette notifications, and shows the source, trust tier and retrieval date for every claim. **Information only, not legal, tax or investment advice.**

**Live demo:** https://civicstack-skjzxntkvqpfepsay56gn7.streamlit.app
(The free Gemini quota is shared. If a quota message appears, use the "Test results" tab, which needs no API call.)

Built for the Prompt Engineering mini project (SCSE4041), Bennett University. Team: Aadya Gupta, Rajan Ahuja, Garvit Narang.

## Why it exists
Official texts are correct but long and scattered. Blogs are readable but often outdated. A plain chatbot answers from memory with no source: on our test set the baseline said a Registrar decision takes "24 hours", while the rule (G.S.R. 107(E)) says thirty days.

## How it works
Three prompts in a chain, plus two code guards:

1. **P1 Query understanding** classifies intent and rewrites the question as a search query (JSON).
2. **Hybrid retrieval** (BAAI/bge-small-en-v1.5 + ChromaDB, and BM25, merged by reciprocal rank fusion, tier weights 1.0 / 0.85 / 0.7) over 926 chunks from 13 documents.
3. **P2 Grounded answer** uses only the retrieved context and cites every claim.
4. **P3 Verifier** checks each claim against its cited passage and removes or softens unsupported ones.

Guards: out-of-scope questions (investment, tax avoidance, legal advice) get a fixed refusal; questions about common delays are answered only from Tier 3 feedback, and with none a fixed reply says so. Model: Gemini 2.5 Flash, temperature 0.0.

See `docs/architecture.md` for the diagram.

## Results
16 test questions with ground truth from the Tier 1 texts, scored 0 to 2 on correctness, faithfulness, citation accuracy, completeness and behaviour.

| | Total /160 | Passed | Citation accuracy |
|---|---|---|---|
| Baseline V1 (no retrieval) | 64 | 4 of 16 | 0.06 |
| Final | 132 | 11 of 16 | 1.75 |

Final scored higher on 14 questions, tied on Q05 and lost on Q06. Scores were assigned with help from an AI model and not independently audited, so read them as a trend. Per-question results are in `test-data/`.

## Setup
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```
Create a `.env` file with `GEMINI_API_KEY=your_key` (never commit it).

```bash
python -m src.ingest                       # build the index from data/
python -m src.pipeline "What is the fee for DIR-3 KYC?" v4
streamlit run app.py
python -m eval.run_eval --versions v1 v4 --judge
```

## Repository guide
- `src/`, `app.py`: the running code (`code/` holds a reference copy of the main modules)
- `prompts/v1` to `v3`: older prompt versions; `prompts/final`: the three final prompts
- `data/`: source documents and `sources.yaml`; `data/feedback/feedback.csv` is the (currently empty) Tier 3 feedback
- `eval/`, `test-data/`: test questions, ground truth and saved scores
- `docs/`: architecture, prompt log, contribution log, Milestone 2 report
- `CHANGELOG.md`: dated list of changes

## Known limitations
- Broad questions ("which / what filings") retrieve too little context (Q05, Q06, Q09).
- The Incorporation Rules are the 2014 as-notified text, so some answers repeat forms since omitted.
- No Tier 3 feedback yet, so "common problems" questions can only return "none found".
- Small evaluation: 16 questions, one run.
- English only. Practitioner (Tier 2) figures are not always labelled unconfirmed.

## Responsible use
No personal data is stored or needed; the app warns users not to enter PAN, Aadhaar or other personal data. Sources are cited, not republished. Rules and fees change, so every answer shows the source date and tells the user to verify on the MCA portal or with a CA/CS.
