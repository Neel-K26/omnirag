from models.schemas import Chunk, ChunkMetadata, DocumentSourceType
from retrieval.reranker import rerank


def _chunk(chunk_id: str, text: str) -> Chunk:
    return Chunk(
        id=chunk_id,
        text=text,
        metadata=ChunkMetadata(
            document_id="d", document_title="t", source_type=DocumentSourceType.text, page=None, chunk_index=0
        ),
    )


def test_rerank_orders_by_relevance():
    chunks = [
        _chunk("a", "The Eiffel Tower is located in Paris, France."),
        _chunk("b", "Hypertension is a major risk factor for stroke and cardiovascular disease."),
        _chunk("c", "Bananas are a good source of potassium."),
    ]
    results = rerank("What is a risk factor for stroke?", chunks, top_n=3)
    assert len(results) == 3
    assert results[0][0].id == "b"
    scores = [s for _, s in results]
    assert scores == sorted(scores, reverse=True)


def test_rerank_top_n_limits_results():
    chunks = [_chunk(str(i), f"document number {i} about clinical topic {i}") for i in range(5)]
    results = rerank("clinical topic 3", chunks, top_n=2)
    assert len(results) == 2


def test_rerank_empty_chunks_returns_empty():
    assert rerank("query", []) == []
