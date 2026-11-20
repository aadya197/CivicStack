# Prompt and pipeline version log

Eight saved versions. Evidence: docs/*.txt, eval/results/*.csv, eval/results/scores_all_versions.csv.

| Version | Date | What changed | Why (failure seen) | Result |
|---|---|---|---|---|
| V1 | 29 Oct 2026 | Baseline: the question alone, no retrieval, no instructions (src/prompts/v1_baseline.txt). | Reference point for comparison. | Confident answers with no source; some stated from memory and wrong (for example 'within 24 hours' for the Central Processing Centre). |
| V2 | 29 Oct 2026 | Retrieved chunks inserted as CONTEXT with a basic 'use the context' instruction (v2_basic_rag.txt). | Ground answers in documents. | Answers grounded, but no citations and no refusal rule. |
| V3 | 29 Oct 2026 | Added citation rule [S#], refusal when the context lacks the answer, source-tier rules and a fixed output format (v3_cited.txt). | Make claims checkable and stop invented facts. | Cited answers, but a practitioner fee table was presented as official. |
| V4 | 29 Oct 2026 | Three-stage chain: query understanding (JSON), grounded answer (answer_v4.txt), verifier (verifier.txt); fixed refusal for out-of-scope questions; disclaimer appended. | One prompt cannot route, ground and check. | Verifier confirmed the directors answer; the fee question was still over-confident. |
| V4.1 | 30-31 Oct 2026 | Rule 7 in answer_v4.txt: fees, penalties, deadlines and processing times as fact only with Tier 1 support; otherwise 'a practitioner source reports ..., not confirmed'. Default output limit raised. | V4 called a practitioner fee table the 'exact' government fee; the baseline output stopped mid-sentence. | Rerun: V4 says no exact fee was found and flags the figures as reported. |
| V4.2 | 2-3 Nov 2026 | Context quality: Tier 1 notifications and Rules added; English-only filter applied to Gazette PDFs. | Hindi text extracted as noise (165 garbled chunks); official text missing from the index. | Garbled chunks 165 to 1; name-extension and CPC answers now cite Tier 1. |
| V4.3 | 12-13 Nov 2026 | Superseded as-enacted Act removed (1,495 to 926 chunks); results of the rewritten and the original query merged; 'Private Limited' normalized to the Act's 'private company'; rule 7b: never quote the instructions. | Q13 answered 'not found' although s.2(68) was indexed (rank 10 for the original wording); Q12 quoted its own instructions. | Normalization moved the chunk from rank 10 to 4; Q13 4 to 10; leak gone; five-question total 38 to 43 of 50. |
| V4.4 | 17 Nov 2026 | Guard in pipeline.py: questions about common delays or rejections are answered only from Tier 3 feedback; with none, a fixed 'no reported experience' reply. | Q08 presented blog content as established reasons. | Q08 2 to 10. |
