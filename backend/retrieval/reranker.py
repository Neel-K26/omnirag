from cohere_client import get_cohere_client
from models.schemas import Chunk

RERANK_MODEL = "rerank-english-v3.0"


def rerank(query: str, chunks: list[Chunk], top_n: int = 5) -> list[tuple[Chunk, float]]:
    if not chunks:
        return []

    client = get_cohere_client()
    response = client.rerank(
        model=RERANK_MODEL,
        query=query,
        documents=[c.text for c in chunks],
        top_n=min(top_n, len(chunks)),
    )
    return [(chunks[result.index], result.relevance_score) for result in response.results]
