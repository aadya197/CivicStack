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
