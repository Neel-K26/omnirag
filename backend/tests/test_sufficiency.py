from generation.sufficiency import check_sufficiency
from models.schemas import Chunk, ChunkMetadata, DocumentSourceType


def _chunk(chunk_id: str, text: str) -> Chunk:
    return Chunk(
        id=chunk_id,
        text=text,
        metadata=ChunkMetadata(
            document_id="d", document_title="t", source_type=DocumentSourceType.text, page=None, chunk_index=0
        ),
    )


def test_check_sufficiency_empty_chunks_short_circuits():
    result = check_sufficiency("What is hypertension?", [])
    assert result.sufficient is False
    assert result.reformulated_query == "What is hypertension?"


def test_check_sufficiency_clear_answer_is_sufficient():
    chunks = [
        _chunk(
            "a",
            "Hypertension is a chronic condition in which blood pressure in the arteries "
            "is persistently elevated, typically defined as 130/80 mmHg or higher.",
        )
    ]
    result = check_sufficiency("What is hypertension?", chunks)
    assert result.sufficient is True
    assert result.reasoning


def test_check_sufficiency_off_topic_chunks_is_insufficient():
    chunks = [
        _chunk("a", "Bananas are a good source of potassium and dietary fiber."),
        _chunk("b", "The Eiffel Tower was completed in 1889 in Paris, France."),
    ]
    result = check_sufficiency("What medications treat type 2 diabetes?", chunks)
    assert result.sufficient is False
    assert result.reformulated_query
