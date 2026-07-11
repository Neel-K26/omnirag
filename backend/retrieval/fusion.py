from models.schemas import Chunk


def reciprocal_rank_fusion(rankings: list[list[Chunk]], k: int = 60) -> list[tuple[Chunk, float]]:
    """Standard RRF: score(d) = sum over rankings containing d of 1 / (k + rank(d)), rank 1-indexed."""
    scores: dict[str, float] = {}
    chunk_by_id: dict[str, Chunk] = {}

    for ranking in rankings:
        for rank, chunk in enumerate(ranking, start=1):
            scores[chunk.id] = scores.get(chunk.id, 0.0) + 1.0 / (k + rank)
            chunk_by_id[chunk.id] = chunk

    fused = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    return [(chunk_by_id[chunk_id], score) for chunk_id, score in fused]
