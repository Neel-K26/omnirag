from generation import adaptive
from models.schemas import (
    Chunk,
    ChunkMetadata,
    DocumentSourceType,
    QueryIntent,
    RetrievalStrategy,
    RoutingDecision,
    SufficiencyResult,
)


def _chunk(chunk_id: str, text: str = "text") -> Chunk:
    return Chunk(
        id=chunk_id,
        text=text,
        metadata=ChunkMetadata(
            document_id="d", document_title="t", source_type=DocumentSourceType.text, page=None, chunk_index=0
        ),
    )


def test_adaptive_stops_after_first_hop_when_sufficient(monkeypatch):
    monkeypatch.setattr(
        adaptive,
        "route_query",
        lambda q: RoutingDecision(intent=QueryIntent.factual, strategy=RetrievalStrategy.hybrid_rerank, method="rule"),
    )
    monkeypatch.setattr(adaptive, "retrieve", lambda query, strategy, top_k: [(_chunk("a", "answer text"), 0.9)])
    monkeypatch.setattr(
        adaptive, "check_sufficiency", lambda query, chunks: SufficiencyResult(sufficient=True, reasoning="good")
    )

    result = adaptive.adaptive_retrieve("some query")
    assert len(result.hops) == 1
    assert result.hops[0].sufficiency.sufficient is True
    assert len(result.final_chunks) == 1


def test_adaptive_reformulates_and_retries_on_insufficient(monkeypatch):
    monkeypatch.setattr(
        adaptive,
        "route_query",
        lambda q: RoutingDecision(intent=QueryIntent.factual, strategy=RetrievalStrategy.hybrid_rerank, method="rule"),
    )

    calls: list[str] = []

    def fake_retrieve(query, strategy, top_k):
        calls.append(query)
        if len(calls) == 1:
            return [(_chunk("a", "partial info"), 0.5)]
        return [(_chunk("b", "complete info"), 0.9)]

    monkeypatch.setattr(adaptive, "retrieve", fake_retrieve)

    sufficiency_calls: list[list[Chunk]] = []

    def fake_check(query, chunks):
        sufficiency_calls.append(chunks)
        if len(sufficiency_calls) == 1:
            return SufficiencyResult(sufficient=False, reasoning="missing detail", reformulated_query="more specific query")
        return SufficiencyResult(sufficient=True, reasoning="now sufficient")

    monkeypatch.setattr(adaptive, "check_sufficiency", fake_check)

    result = adaptive.adaptive_retrieve("vague query")
    assert len(result.hops) == 2
    assert calls == ["vague query", "more specific query"]
    assert result.hops[0].sufficiency.sufficient is False
    assert result.hops[1].sufficiency.sufficient is True
    assert {c.id for c in result.final_chunks} == {"a", "b"}


def test_adaptive_caps_at_max_hops_even_if_still_insufficient(monkeypatch):
    monkeypatch.setattr(
        adaptive,
        "route_query",
        lambda q: RoutingDecision(intent=QueryIntent.analytical, strategy=RetrievalStrategy.dense, method="rule"),
    )
    monkeypatch.setattr(adaptive, "retrieve", lambda query, strategy, top_k: [(_chunk("x", "still incomplete"), 0.4)])
    monkeypatch.setattr(
        adaptive,
        "check_sufficiency",
        lambda query, chunks: SufficiencyResult(sufficient=False, reasoning="never enough", reformulated_query="try again"),
    )

    result = adaptive.adaptive_retrieve("query")
    assert len(result.hops) == adaptive.MAX_HOPS
    assert result.hops[-1].sufficiency.sufficient is False


def test_adaptive_retrieve_live_end_to_end(monkeypatch, populated_store):
    from retrieval import hybrid

    monkeypatch.setattr(hybrid, "get_vector_store", lambda: populated_store)

    result = adaptive.adaptive_retrieve("What medications treat high blood pressure?")
    assert result.routing.intent in QueryIntent
    assert 1 <= len(result.hops) <= adaptive.MAX_HOPS
    assert len(result.final_chunks) > 0
    assert result.hops[0].sufficiency.reasoning
