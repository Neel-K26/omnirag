from models.schemas import RetrievalStrategy
from retrieval import hybrid


def test_dense_only(monkeypatch, populated_store):
    monkeypatch.setattr(hybrid, "get_vector_store", lambda: populated_store)
    results = hybrid.dense_only("What raises the risk of stroke?", top_k=3)
    assert len(results) == 3
    assert "Hypertension" in results[0][0].text


def test_sparse_only(monkeypatch, populated_store):
    monkeypatch.setattr(hybrid, "get_vector_store", lambda: populated_store)
    results = hybrid.sparse_only("blood pressure ACE inhibitors", top_k=3)
    assert len(results) == 3
    assert any("ACE inhibitors" in c.text for c, _ in results)


def test_hybrid_fused_combines_both_signals(monkeypatch, populated_store):
    monkeypatch.setattr(hybrid, "get_vector_store", lambda: populated_store)
    results = hybrid.hybrid_fused("blood pressure treatment", top_k=5)
    assert 0 < len(results) <= 5
    result_ids = {c.id for c, _ in results}
    assert "0" in result_ids or "4" in result_ids


def test_hybrid_rerank_orders_most_relevant_first(monkeypatch, populated_store):
    monkeypatch.setattr(hybrid, "get_vector_store", lambda: populated_store)
    results = hybrid.hybrid_rerank("What treats high blood pressure?", top_k=3)
    assert len(results) == 3
    top_text = results[0][0].text.lower()
    assert "blood pressure" in top_text or "ace inhibitors" in top_text
    scores = [s for _, s in results]
    assert scores == sorted(scores, reverse=True)


def test_retrieve_dispatches_by_strategy(monkeypatch, populated_store):
    monkeypatch.setattr(hybrid, "get_vector_store", lambda: populated_store)
    for strategy in RetrievalStrategy:
        results = hybrid.retrieve("stroke risk factors", strategy=strategy, top_k=2)
        assert len(results) == 2
