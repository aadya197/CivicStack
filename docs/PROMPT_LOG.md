# Prompt version log
Record every meaningful change. Evidence for "iteration" marks.

| Version | Date | Change | Why (failure observed) | Test IDs affected | Result |
|---|---|---|---|---|---|
| V1 | | Baseline, no retrieval | Starting point | | |
| V2 | | Added retrieved context | | | |
| V3 | | Citations + refusal + tier rules | | | |
| V4 | | Query understanding + verifier chain | | | |
| V4.1 | 2026-11-12 | Removed the superseded as-enacted Companies Act from the index (1,495 to 926 chunks) | Q13 V4 said "could not find"; context lacked the s.2(68) 200-member limit; duplicate Act versions crowded out relevant chunks | Q13, Q02 | commit df387cf; retrieval check now returns the s.2(68) chunk for two of three test queries |
| V4.2 | 2026-11-13 | V4 retrieves with the rewritten query and the original question, merges up to 8 chunks | Rewritten queries can drift away from the legal definition | Q13 | rerun pending |
| V4.1 | 2026-11-12 | Removed the superseded as-enacted Companies Act from the index (1,495 to 926 chunks) | Q13 V4 said "could not find"; context lacked the s.2(68) 200-member limit; duplicate Act versions crowded out relevant chunks | Q13, Q02 | commit df387cf; retrieval check now returns the s.2(68) chunk for two of three test queries |
| V4.2 | 2026-11-13 | V4 retrieves with the rewritten query and the original question, merges up to 8 chunks | Rewritten queries can drift away from the legal definition | Q13 | rerun pending |
| V4.3 | 2026-11-13 | (a) interleaved merge of rewritten-query and original-question results; (b) query normalization mapping "Private Limited" to the Act's "private company"; (c) rule 7b: never mention the instructions | Q13 V4: the s.2(68) 200-member limit was not retrieved; Q12 V4 quoted its own instructions | Q13, Q12 | Interleaving alone did not change retrieval (chunk absent from the top 8 either way). Normalization moved the s.2(68) chunk from rank 10 to rank 4. End-to-end rerun pending API quota |
