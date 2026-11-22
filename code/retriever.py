"""Hybrid retrieval: dense (Chroma) + BM25, fused with Reciprocal Rank Fusion,
then re-weighted by source tier so official sources win ties."""
import json
import re
from collections import defaultdict

import numpy as np
from rank_bm25 import BM25Okapi

from src import config


def _tok(t: str):
    return re.findall(r"\w+", t.lower())


class Retriever:
    def __init__(self):
        import chromadb
        from sentence_transformers import SentenceTransformer

        path = config.PROCESSED_DIR / "chunks.jsonl"
        if not path.exists():
            raise FileNotFoundError("Index not built. Run: python -m src.ingest")
        self.chunks = {}
        for line in open(path, encoding="utf-8"):
            c = json.loads(line)
            self.chunks[c["id"]] = c
        self.ids = list(self.chunks)
        self.bm25 = BM25Okapi([_tok(self.chunks[i]["text"]) for i in self.ids])
        self.model = SentenceTransformer(config.EMBED_MODEL)
        client = chromadb.PersistentClient(path=str(config.INDEX_DIR / "chroma"))
        self.col = client.get_collection("incorp")

    @staticmethod
    def _applies(chunk, entity_types):
        if not entity_types:
            return True
        et = set(chunk.get("entity_types") or ["all"])
        return "all" in et or bool(et & set(entity_types))

    def search(self, query, entity_types=None, k=config.TOP_K):
        q = self.model.encode(config.QUERY_PREFIX + query, normalize_embeddings=True)
        n = min(config.CANDIDATES, len(self.ids))
        dense = self.col.query(query_embeddings=[q.tolist()], n_results=n)["ids"][0]
        scores = self.bm25.get_scores(_tok(query))
        sparse = [self.ids[i] for i in np.argsort(scores)[::-1][:n] if scores[i] > 0]

        fused = defaultdict(float)
        for ranked in (dense, sparse):
            for r, cid in enumerate(ranked):
                fused[cid] += 1.0 / (config.RRF_K + r)

        results = []
        for cid, s in fused.items():
            c = self.chunks[cid]
            if not self._applies(c, entity_types):
                continue
            results.append((s * config.TIER_WEIGHT.get(int(c["tier"]), 0.7), c))
        results.sort(key=lambda x: -x[0])
        return [dict(c, score=round(s, 5)) for s, c in results[:k]]
