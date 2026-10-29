import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
FEEDBACK_CSV = DATA_DIR / "feedback" / "feedback.csv"
SOURCES_YAML = DATA_DIR / "sources.yaml"
PROCESSED_DIR = DATA_DIR / "processed"
INDEX_DIR = ROOT / "index"

EMBED_MODEL = os.getenv("EMBED_MODEL", "BAAI/bge-small-en-v1.5")
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-2.5-flash")

# Chunking (words, not tokens: simple and reproducible). Treat as tunable experiments.
CHUNK_WORDS = 350
CHUNK_OVERLAP = 60

# Retrieval
TOP_K = 6
CANDIDATES = 30
RRF_K = 60
# Tier 1 = official, 2 = practitioner, 3 = reported experience
TIER_WEIGHT = {1: 1.0, 2: 0.85, 3: 0.7}

ENTITY_TYPES = ["pvt_ltd", "llp", "opc", "public_ltd", "section_8",
                "partnership", "sole_prop", "all"]
