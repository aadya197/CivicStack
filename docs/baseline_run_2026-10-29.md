# CivicStack: Baseline Run Log

Date: 29 October 2026 | Milestone 2 deadline: 2 November 2026 | Project: RAG assistant for company registration in India

This log records what was actually built and run on day 1, including failures. Use it as evidence for the technical document, the report and the demo video.

## 1. System state at end of day

| Item | Status |
| --- | --- |
| Repository scaffold (CivicStack) | Built, running locally |
| LLM | Gemini API (model set in `.env` as `LLM_MODEL`) |
| Embeddings | BAAI/bge-small-en-v1.5 (local) |
| Vector store and keyword index | ChromaDB plus BM25, fused with RRF, tier-weighted |
| Knowledge base | 595 chunks from 3 enabled sources |
| Prompt versions | V1 baseline, V2 basic RAG, V3 cited, V4 chain (query understanding, answer, verifier) |

### Sources currently indexed

| Source | Tier | Note |
| --- | --- | --- |
| Companies Act 2013, Gazette copy (PDF, 294 pages) | 1 | As enacted in 2013, not the amended text |
| Razorpay Rize: SPICe+ FAQ | 2 | Practitioner article |
| incorpx: SPICe+ guide 2026 | 2 | Practitioner article, contains fee and timeline figures |

No current fee rules or MCA process pages are indexed yet.

## 2. Setup problems met and fixed

These belong in the implementation chapter of the report.

1. `ImportError: cannot import name 'genai' from 'google'`: dependencies had not been installed into the active Python. Fixed by creating a virtual environment and using `python -m pip install -r requirements.txt`.
2. `AttributeError: 'list' object has no attribute 'get'`: `sources.yaml` was a bare list. Fixed by keeping `sources:` as the top-level key and by making the loader accept both layouts.
3. `TypeError: Object of type date is not JSON serializable`: YAML parsed an unquoted date as a date object. Fixed by converting `date_retrieved` to a string.
4. `[skip] ... No such file`: the PDF was named `Companies Act 2013.pdf` (spaces) while `sources.yaml` expected `Companies_Act_2013.pdf`. Fixed by renaming the file.
5. Ingestion then succeeded: `Indexed 595 chunks.`

## 3. Experiment 1: retrieval check

Query: "minimum number of directors in a private company"

- The top 6 results were all from the Act and all about directors, the board, the private company definition or independent directors.
- A text check for the phrase "two directors" was True for the rank-1 chunk (`companies-act-2013-enacted-186`) and False for the other five. The answer-bearing chunk was therefore retrieved at rank 1.
- Scores around 0.03 are fused rank scores, so only their order is meaningful.

## 4. Experiment 2: easy factual question across prompt versions

Question: "How many directors must a private company have?"

| Version | Answer | Sources shown | Observation |
| --- | --- | --- | --- |
| V1 | Minimum of two; maximum fifteen | None | Correct, but nothing to verify against |
| V2 | Minimum of two | Cited "Section 149(1)(a)" in free text | Correct. The strings "149" and "fifteen" were present in the retrieved context, so the section number was not invented |
| V3 | Minimum of two, with details | \[S1\] | Correct, cited |
| V4 | Minimum of two, with details, no reported experience, disclaimer | \[S1\] | Correct, cited, disclaimer added |

Verifier trace (V4): all three claims in the draft were marked supported, each with a note pointing to Section 149.

Takeaway: easy questions do not separate the versions. V1 also gets this right from memory. The value of retrieval only shows on questions where the model's memory is unreliable or where a source is needed.

Open point: the V4 answer from the first run included a "maximum fifteen" bullet, while the draft shown in the later trace did not. Output can vary between runs, so consistency should be tested with repeated runs.

## 5. Experiment 3: fee question (key finding)

Question: "What is the exact government fee for registering a Private Limited company today?"

| Version | Behaviour |
| --- | --- |
| V1 | Gives specific fee figures confidently from memory, says they are "generally stable", cites nothing, and the output was cut off mid-sentence ("Up to") |
| V3 | Gives a fee table by authorized capital, all cited to \[S3\], the incorpx blog (Tier 2) |
| V4 | Same table, labelled "exact government fee", cited to \[S3\], with the retrieval date shown |

### Failures identified

1. **Over-confidence from a Tier 2 source.** V3 and V4 present practitioner-blog figures as the exact government fee. No Tier 1 source supports them in the index. The figures have not been verified against MCA and must not be treated as correct.
2. **Misleading date.** The date shown is the day the page was scraped, not the date the figures were valid.
3. **V1 truncation.** Long answers are cut off, most likely because the output token limit is too low for the model's behaviour.
4. **Citations are hard to check.** All Act chunks show the same file path. Page numbers are not stored.

## 6. Planned fixes (not yet applied)

| Fix | Change | How to verify |
| --- | --- | --- |
| F1: Tier-aware rule for money and time figures | Add a rule to `answer_v4.txt`: state fees, penalties, deadlines and processing times as fact only if a Tier 1 source supports them; otherwise say a practitioner source reports the figure and it could not be confirmed officially; never call a figure "exact" without Tier 1 support | Rerun the fee question on V4 and compare before and after |
| F2: Raise output limit | Raise the default `max_tokens` in `src/llm.py` to 8192 | Rerun V1 on the fee question and check it is no longer cut off |
| F3: Add Tier 1 fee and process sources | Download the Companies (Registration Offices and Fees) Rules, 2014, the Incorporation Rules and MCA process pages into `data/raw/`, add to `sources.yaml` as Tier 1, re-ingest | Rerun the fee question and compare against the Tier 2 figures; record any disagreement |
| F4: Page numbers in citations | Store the page number per chunk during ingestion and show it in the source list | Check that a citation can be located in the PDF |

Each fix should be logged as a prompt or pipeline version in `docs/PROMPT_LOG.md`, with the failing example and the result after the change.

## 7. Plan for 30 October

1. Apply F1 and F2, rerun the fee question, and save before and after outputs.
2. Download Tier 1 sources (MCA rules, fee rules, LLP Act, Startup India page) and add them to `sources.yaml`; re-ingest and note the new chunk count.
3. Add 3 to 5 more Tier 2 guides covering LLP, OPC, Section 8 and partnership.
4. Message a CA/CS, a recent founder and a senior; record paraphrased answers in `data/feedback/feedback.csv`, with no personal data.
5. Apply F4 (page numbers).
6. Start the ground truth for `eval/test_set.csv`, written from Tier 1 sources only.
7. Commit and push to GitHub with descriptive messages.

## 8. Contribution log (for viva evidence)

| Date | Work done | Evidence |
| --- | --- | --- |
| 29 Oct 2026 | Faculty approval obtained; environment and Gemini API set up; Companies Act PDF added; knowledge base indexed (595 chunks); retrieval test; V1 to V4 baseline runs; fee-question failure analysis | This log; terminal outputs; repository commit history |

## 9. Guideline mapping

- Iteration evidence: prompt versions V1 to V4 and fixes F1 to F4.
- Evaluation: retrieval check, factual question, fee question; the formal test set and rubric are still to be completed.
- Reliability and limitations: Tier 2 over-confidence, stale or as-enacted sources, output variation.
- Responsible AI: information-only disclaimer, source tiers, no personal data in prompts, no fabricated feedback.
