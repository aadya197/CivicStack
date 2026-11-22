# Changelog

## 2026-11-22
- Deployed the Streamlit app (Ask, Compare V1 vs V4, Test results, About) for public testing.
- Fixed Gemini API version error (use v1beta for system instructions).
- Added retry on 503 errors and a fallback model.
- Added Milestone 2 report, prompt sheets and test table.

## 2026-11-17
- V4.4: guard for questions about common delays or rejections (answered only from Tier 3 feedback; fixed reply when none exists). Q08 score 2 to 10.
- Completed the 16-question evaluation (baseline 64/160, final 132/160).
- Added the first version of the Streamlit app.

## 2026-11-12 to 2026-11-13
- V4.3: removed the superseded Act text (1,495 to 926 chunks), merged results of rewritten and original queries, normalised "Private Limited" to the Act's wording, added rule 7b.

## 2026-11-02 to 2026-11-03
- V4.2: added official Gazette notifications and Rules; English-only filter removed Hindi noise (165 garbled chunks to 1).

## 2026-10-30 to 2026-10-31
- V4.1: rule 7, fees and deadlines stated as fact only with Tier 1 support.

## 2026-10-29
- V1 to V4: baseline, basic RAG, cited answers, three-prompt chain (query understanding, grounded answer, verifier).
