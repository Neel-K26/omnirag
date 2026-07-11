import fitz
from fastapi.testclient import TestClient

import ingestion.pipeline as pipeline
import routers.documents as documents_router
from ingestion.embeddings import get_embedding_dim
from ingestion.registry import DocumentRegistry
from ingestion.store import VectorStore
from main import app

client = TestClient(app)


def _fresh_pipeline_state(monkeypatch):
    store = VectorStore(dim=get_embedding_dim())
    registry = DocumentRegistry()
    monkeypatch.setattr(pipeline, "get_vector_store", lambda: store)
    monkeypatch.setattr(pipeline, "get_document_registry", lambda: registry)
    monkeypatch.setattr(documents_router, "get_document_registry", lambda: registry)
    monkeypatch.setattr(store, "save", lambda *a, **k: None)
    monkeypatch.setattr(registry, "save", lambda *a, **k: None)
    return store, registry


def test_upload_text_and_list_documents(monkeypatch):
    _fresh_pipeline_state(monkeypatch)

    resp = client.post(
        "/documents/text",
        json={"text": "Hypertension is persistently elevated blood pressure. " * 5, "title": "Test Doc"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["document"]["title"] == "Test Doc"
    assert body["document"]["num_chunks"] > 0
    assert len(body["chunks"]) == body["document"]["num_chunks"]

    list_resp = client.get("/documents")
    assert list_resp.status_code == 200
    assert "Test Doc" in [d["title"] for d in list_resp.json()]


def test_upload_text_rejects_empty(monkeypatch):
    _fresh_pipeline_state(monkeypatch)
    resp = client.post("/documents/text", json={"text": "   ", "title": "Empty"})
    assert resp.status_code == 400


def test_upload_pdf(monkeypatch):
    _fresh_pipeline_state(monkeypatch)

    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Hypertension is a chronic condition of elevated blood pressure.", fontsize=11)
    pdf_bytes = doc.tobytes()
    doc.close()

    resp = client.post("/documents/pdf", files={"file": ("test.pdf", pdf_bytes, "application/pdf")})
    assert resp.status_code == 200
    body = resp.json()
    assert body["document"]["source_type"] == "pdf"
    assert body["document"]["num_chunks"] >= 1
    assert body["chunks"][0]["metadata"]["page"] == 1


def test_upload_pdf_rejects_non_pdf_filename(monkeypatch):
    _fresh_pipeline_state(monkeypatch)
    resp = client.post("/documents/pdf", files={"file": ("test.txt", b"hello", "text/plain")})
    assert resp.status_code == 400
