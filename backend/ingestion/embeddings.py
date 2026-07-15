import numpy as np

from cohere_client import get_cohere_client

# 384-dim — matches the previous local sentence-transformers model's dimension, so the FAISS
# index construction code needed no changes, though the vector *values* are from a completely
# different embedding space (Cohere's, not sentence-transformers'), so any previously-ingested
# documents still need re-ingestion after this switch.
MODEL_NAME = "embed-english-light-v3.0"
EMBEDDING_DIM = 384


def _embed(texts: list[str], input_type: str) -> np.ndarray:
    client = get_cohere_client()
    response = client.embed(
        model=MODEL_NAME,
        input_type=input_type,
        texts=texts,
        embedding_types=["float"],
    )
    return np.array(response.embeddings.float, dtype="float32")


def embed_documents(texts: list[str]) -> np.ndarray:
    """Embeds text being indexed (document chunks) — use at ingestion time."""
    return _embed(texts, input_type="search_document")


def embed_query(text: str) -> np.ndarray:
    """Embeds a search query — use at retrieval time. Cohere scores document/query pairs
    better when each side is embedded with its matching input_type, so this is not
    interchangeable with embed_documents even though the output shape is the same."""
    return _embed([text], input_type="search_query")[0]


def get_embedding_dim() -> int:
    return EMBEDDING_DIM
