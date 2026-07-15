import pytest

from ingestion.embeddings import embed_documents
from ingestion.store import VectorStore
from models.schemas import Chunk, ChunkMetadata, DocumentSourceType

SAMPLE_TEXTS = [
    "Hypertension is persistently elevated blood pressure and a major risk factor for stroke and heart failure.",
    "Diabetes mellitus is characterized by elevated blood glucose levels and can damage blood vessels over time.",
    "Regular aerobic exercise improves cardiovascular health and helps lower blood pressure.",
    "Antibiotic resistance occurs when bacteria evolve mechanisms that reduce drug effectiveness.",
    "ACE inhibitors and calcium channel blockers are commonly used to treat high blood pressure.",
]


@pytest.fixture
def populated_store() -> VectorStore:
    chunks = [
        Chunk(
            id=str(i),
            text=t,
            metadata=ChunkMetadata(
                document_id="doc1",
                document_title="Test Doc",
                source_type=DocumentSourceType.text,
                page=None,
                chunk_index=i,
            ),
        )
        for i, t in enumerate(SAMPLE_TEXTS)
    ]
    embeddings = embed_documents(SAMPLE_TEXTS)
    store = VectorStore(dim=embeddings.shape[1])
    store.add(chunks, embeddings)
    return store
