import routers.benchmark as benchmark_router
from generation.adaptive import adaptive_retrieve
from models.schemas import (
    AdaptiveRetrievalResult,
    Chunk,
    ChunkMetadata,
    DocumentSourceType,
    QueryIntent,
    RagasScores,
    RetrievalStrategy,
    RoutingDecision,
)


def _chunk(chunk_id: str, text: str = "text") -> Chunk:
    return Chunk(
        id=chunk_id,
        text=text,
        metadata=ChunkMetadata(
            document_id="d", document_title="t", source_type=DocumentSourceType.text, page=None, chunk_index=0
        ),
    )


def test_run_benchmark_aggregates_mean_correctly(monkeypatch):
    monkeypatch.setattr(benchmark_router, "BENCHMARK_QUERIES", ["query one", "query two", "query three"])

    routing = RoutingDecision(intent=QueryIntent.factual, strategy=RetrievalStrategy.hybrid_rerank, method="rule")

    def fake_adaptive_retrieve(query: str) -> AdaptiveRetrievalResult:
        return AdaptiveRetrievalResult(routing=routing, hops=[], final_chunks=[_chunk("a", "some context")])

    monkeypatch.setattr(benchmark_router, "adaptive_retrieve", fake_adaptive_retrieve)
    monkeypatch.setattr(benchmark_router, "stream_answer", lambda query, chunks: iter(["mock ", "answer"]))

    scores_by_query = {
        "query one": RagasScores(faithfulness=1.0, answer_relevancy=0.8, context_precision=0.6),
        "query two": RagasScores(faithfulness=0.5, answer_relevancy=0.4, context_precision=0.3),
        "query three": RagasScores(faithfulness=0.0, answer_relevancy=0.2, context_precision=0.9),
    }
    monkeypatch.setattr(
        benchmark_router, "evaluate_response", lambda query, answer, contexts: scores_by_query[query]
    )

    result = benchmark_router.run_benchmark()

    assert len(result.results) == 3
    assert all(r.answer == "mock answer" for r in result.results)
    assert all(r.num_hops == 0 for r in result.results)

    assert result.aggregate.faithfulness == round((1.0 + 0.5 + 0.0) / 3, 4)
    assert result.aggregate.answer_relevancy == round((0.8 + 0.4 + 0.2) / 3, 4)
    assert result.aggregate.context_precision == round((0.6 + 0.3 + 0.9) / 3, 4)
    assert result.aggregate_latency_ms >= 0


def test_run_benchmark_handles_empty_chunks_without_calling_ragas(monkeypatch):
    monkeypatch.setattr(benchmark_router, "BENCHMARK_QUERIES", ["unanswerable query"])

    routing = RoutingDecision(intent=QueryIntent.factual, strategy=RetrievalStrategy.hybrid_rerank, method="rule")
    monkeypatch.setattr(
        benchmark_router,
        "adaptive_retrieve",
        lambda query: AdaptiveRetrievalResult(routing=routing, hops=[], final_chunks=[]),
    )
    monkeypatch.setattr(benchmark_router, "stream_answer", lambda query, chunks: iter(["no context available"]))

    def fail_if_called(*args, **kwargs):
        raise AssertionError("evaluate_response should not be called when there are no chunks")

    monkeypatch.setattr(benchmark_router, "evaluate_response", fail_if_called)

    result = benchmark_router.run_benchmark()
    assert result.results[0].ragas == RagasScores(faithfulness=0.0, answer_relevancy=0.0, context_precision=0.0)
