from models.schemas import Chunk, ChunkMetadata, DocumentSourceType
from retrieval.fusion import reciprocal_rank_fusion


def _chunk(chunk_id: str, text: str = "text") -> Chunk:
    return Chunk(
        id=chunk_id,
        text=text,
        metadata=ChunkMetadata(
            document_id="d", document_title="t", source_type=DocumentSourceType.text, page=None, chunk_index=0
        ),
    )


def test_rrf_favors_items_ranked_high_in_both_lists():
    a, b, c, d = _chunk("a"), _chunk("b"), _chunk("c"), _chunk("d")
    ranking1 = [a, b, c, d]
    ranking2 = [b, a, d, c]

    fused = reciprocal_rank_fusion([ranking1, ranking2])
    fused_ids = [chunk.id for chunk, _ in fused]

    assert set(fused_ids[:2]) == {"a", "b"}


def test_rrf_item_only_in_one_list_still_included():
    a, b = _chunk("a"), _chunk("b")
    fused = reciprocal_rank_fusion([[a], [b]])
    assert {chunk.id for chunk, _ in fused} == {"a", "b"}


def test_rrf_scores_decrease_with_rank():
    a, b, c = _chunk("a"), _chunk("b"), _chunk("c")
    fused = reciprocal_rank_fusion([[a, b, c]])
    scores = [s for _, s in fused]
    assert scores == sorted(scores, reverse=True)


def test_rrf_empty_rankings_returns_empty():
    assert reciprocal_rank_fusion([]) == []
    assert reciprocal_rank_fusion([[], []]) == []
