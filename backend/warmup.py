"""Eagerly loads the slow parts of the app (the local embedding model, mainly) instead of
deferring them to whichever request happens to arrive first. Called from main.py's lifespan
at process startup, and also exposed as GET /warmup for an external pinger to re-trigger —
though after the first call within a process it's nearly instant, since the underlying
singletons (get_embedding_model, get_vector_store) are @lru_cache'd.

Does NOT touch Gemini/Cohere: those clients are cheap to construct (no I/O until the first
real API call), and speculatively calling a paid LLM API on every cold start would waste
quota/cost for no benefit — the thing actually slow enough to matter is loading
sentence-transformers' model weights onto CPU.
"""

from ingestion.embeddings import embed_texts
from ingestion.store import get_vector_store


def warmup() -> None:
    embed_texts(["warmup"])
    get_vector_store()
