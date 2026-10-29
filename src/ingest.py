"""Build the knowledge base: fetch/read sources -> chunk -> embed -> index.

Run:  python -m src.ingest
"""
import csv
import datetime as dt
import io
import json
import re
import time
from pathlib import Path
from urllib import robotparser
from urllib.parse import urlparse

import requests
import yaml
from bs4 import BeautifulSoup
from pypdf import PdfReader
from tqdm import tqdm

from src import config

HEADERS = {"User-Agent": "CivicStackBot/0.1 (student project)"}
_robots = {}


def allowed_by_robots(url: str) -> bool:
    root = "{0.scheme}://{0.netloc}".format(urlparse(url))
    if root not in _robots:
        rp = robotparser.RobotFileParser()
        try:
            rp.set_url(root + "/robots.txt")
            rp.read()
        except Exception:
            rp = None
        _robots[root] = rp
    rp = _robots[root]
    return True if rp is None else rp.can_fetch(HEADERS["User-Agent"], url)


def clean(text: str) -> str:
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return text.strip()


def pdf_to_text(data: bytes) -> str:
    reader = PdfReader(io.BytesIO(data))
    return clean("\n\n".join((p.extract_text() or "") for p in reader.pages))


def html_to_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for t in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
        t.decompose()
    return clean(soup.get_text("\n"))


def fetch_url(url: str) -> str:
    if not allowed_by_robots(url):
        raise PermissionError(f"robots.txt disallows {url}")
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    if url.lower().endswith(".pdf") or "pdf" in r.headers.get("content-type", "").lower():
        return pdf_to_text(r.content)
    return html_to_text(r.text)


def read_local(path: Path) -> str:
    suf = path.suffix.lower()
    if suf == ".pdf":
        return pdf_to_text(path.read_bytes())
    raw = path.read_text(encoding="utf-8", errors="ignore")
    return html_to_text(raw) if suf in (".html", ".htm") else clean(raw)


def chunk_text(text: str, size: int = config.CHUNK_WORDS, overlap: int = config.CHUNK_OVERLAP):
    words = text.split()
    if not words:
        return []
    step = max(size - overlap, 1)
    chunks, i = [], 0
    while i < len(words):
        chunks.append(" ".join(words[i:i + size]))
        if i + size >= len(words):
            break
        i += step
    return chunks


def load_documents():
    """Yield (meta, text) for each enabled entry in sources.yaml."""
    cfg = yaml.safe_load(config.SOURCES_YAML.read_text(encoding="utf-8")) or {}
    for s in cfg.get("sources", []):
        if not s.get("enabled", True):
            continue
        try:
            if s.get("path"):
                text = read_local(config.ROOT / s["path"])
            else:
                text = fetch_url(s["url"])
                time.sleep(1.0)  # be polite
        except Exception as e:
            print(f"[skip] {s.get('id')}: {e}")
            continue
        meta = {
            "source_id": s["id"], "source_name": s.get("name", s["id"]),
            "url": s.get("url", s.get("path", "")), "tier": int(s["tier"]),
            "entity_types": s.get("entity_types", ["all"]),
            "topic": s.get("topic", "general"),
            "date_retrieved": s.get("date_retrieved", dt.date.today().isoformat()),
        }
        yield meta, text


def load_feedback_chunks():
    """Tier 3: each row of feedback.csv becomes one chunk (labelled as reported experience)."""
    if not config.FEEDBACK_CSV.exists():
        return
    with open(config.FEEDBACK_CSV, newline="", encoding="utf-8") as f:
        for i, row in enumerate(csv.DictReader(f)):
            if not (row.get("detail") or "").strip():
                continue
            text = (f"Reported experience ({row.get('source_type', 'unknown')}, {row.get('date', '')}): "
                    f"{row.get('issue', '')}. {row['detail']}")
            yield {
                "id": f"fb-{i}", "text": text, "source_id": row.get("id", f"fb-{i}"),
                "source_name": f"Feedback: {row.get('source_type', 'unknown')}",
                "url": "", "tier": 3,
                "entity_types": [e.strip() for e in (row.get("entity_type") or "all").split(";")],
                "topic": row.get("topic", "common_issues"),
                "date_retrieved": row.get("date", ""),
            }


def build_chunks():
    chunks = []
    for meta, text in tqdm(list(load_documents()), desc="documents"):
        for j, c in enumerate(chunk_text(text)):
            chunks.append({"id": f"{meta['source_id']}-{j}", "text": c, **meta})
    chunks.extend(load_feedback_chunks())
    return chunks


def build_index(chunks):
    import chromadb
    from sentence_transformers import SentenceTransformer

    config.INDEX_DIR.mkdir(exist_ok=True)
    config.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    model = SentenceTransformer(config.EMBED_MODEL)
    embs = model.encode([c["text"] for c in chunks], normalize_embeddings=True,
                        batch_size=32, show_progress_bar=True)
    client = chromadb.PersistentClient(path=str(config.INDEX_DIR / "chroma"))
    try:
        client.delete_collection("incorp")
    except Exception:
        pass
    col = client.create_collection("incorp", metadata={"hnsw:space": "cosine"})
    for s in range(0, len(chunks), 500):
        b = chunks[s:s + 500]
        col.add(ids=[c["id"] for c in b], embeddings=embs[s:s + 500].tolist(),
                documents=[c["text"] for c in b],
                metadatas=[{"tier": c["tier"], "source_id": c["source_id"]} for c in b])
    with open(config.PROCESSED_DIR / "chunks.jsonl", "w", encoding="utf-8") as f:
        for c in chunks:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    print(f"Indexed {len(chunks)} chunks.")


if __name__ == "__main__":
    ch = build_chunks()
    if not ch:
        raise SystemExit("No chunks built. Enable sources in data/sources.yaml or add feedback rows.")
    build_index(ch)
