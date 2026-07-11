import json

from fastapi.testclient import TestClient

from main import app
from retrieval import hybrid

client = TestClient(app)


def test_chat_stream_end_to_end(monkeypatch, populated_store):
    monkeypatch.setattr(hybrid, "get_vector_store", lambda: populated_store)

    with client.stream("POST", "/chat/stream", json={"query": "What treats high blood pressure?"}) as resp:
        assert resp.status_code == 200
        events = [json.loads(line) for line in resp.iter_lines() if line]

    types = [e["type"] for e in events]
    assert "routing" in types
    assert "citations" in types
    assert "token" in types
    assert types[-1] == "done"

    done_data = events[-1]["data"]
    assert done_data["response"]
    assert done_data["latency_ms"] > 0
    assert done_data["prompt_tokens"] is not None
    assert done_data["completion_tokens"] is not None
    assert done_data["estimated_cost_usd"] is not None
    assert done_data["estimated_cost_usd"] > 0

    reconstructed = "".join(e["data"] for e in events if e["type"] == "token")
    assert reconstructed == done_data["response"]


def test_chat_stream_rejects_empty_query():
    resp = client.post("/chat/stream", json={"query": "   "})
    assert resp.status_code == 400


def test_chat_evaluate():
    resp = client.post(
        "/chat/evaluate",
        json={
            "query": "What is hypertension?",
            "response": "Hypertension is persistently elevated blood pressure, a major risk factor for stroke.",
            "contexts": [
                "Hypertension is a chronic condition of persistently elevated blood pressure, "
                "a major risk factor for stroke and heart failure."
            ],
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert 0.0 <= body["faithfulness"] <= 1.0
    assert 0.0 <= body["answer_relevancy"] <= 1.0
    assert 0.0 <= body["context_precision"] <= 1.0
