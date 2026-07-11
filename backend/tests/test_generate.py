from generation.generate import build_citations, stream_answer
from models.schemas import Chunk, ChunkMetadata, DocumentSourceType


def _chunk(chunk_id: str, text: str, page: int | None = None) -> Chunk:
    return Chunk(
        id=chunk_id,
        text=text,
        metadata=ChunkMetadata(
            document_id="d", document_title="Hypertension Overview", source_type=DocumentSourceType.text, page=page, chunk_index=0
        ),
    )


def test_build_citations_indexes_from_one():
    chunks = [_chunk("a", "text one", page=1), _chunk("b", "text two", page=2)]
    citations = build_citations(chunks)
    assert [c.index for c in citations] == [1, 2]
    assert citations[0].document_title == "Hypertension Overview"
    assert citations[0].page == 1
    assert citations[0].text == "text one"


def test_build_citations_empty():
    assert build_citations([]) == []


def test_stream_answer_produces_grounded_streaming_text():
    chunks = [
        _chunk(
            "a",
            "Hypertension is persistently elevated blood pressure and a major risk factor for stroke and heart failure.",
        )
    ]
    deltas = list(stream_answer("What is hypertension a risk factor for?", chunks))
    assert len(deltas) > 1  # actually streamed in multiple pieces, not one blob
    full_text = "".join(deltas)
    assert "stroke" in full_text.lower()
