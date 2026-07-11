import uuid

from ingestion.chunking import chunk_text
from ingestion.embeddings import embed_texts
from ingestion.parsers import parse_pdf, parse_text, parse_url
from ingestion.registry import get_document_registry
from ingestion.store import DATA_DIR, get_vector_store
from models.schemas import Chunk, ChunkMetadata, Document, DocumentSourceType

CHUNK_SIZE = 512
CHUNK_OVERLAP = 50


def _build_chunks(document: Document, pages: list[tuple[int | None, str]]) -> list[Chunk]:
    chunks: list[Chunk] = []
    chunk_index = 0
    for page_num, text in pages:
        for piece in chunk_text(text, CHUNK_SIZE, CHUNK_OVERLAP):
            chunks.append(
                Chunk(
                    id=str(uuid.uuid4()),
                    text=piece,
                    metadata=ChunkMetadata(
                        document_id=document.id,
                        document_title=document.title,
                        source_type=document.source_type,
                        page=page_num,
                        chunk_index=chunk_index,
                    ),
                )
            )
            chunk_index += 1
    return chunks


def _embed_and_store(document: Document, chunks: list[Chunk]) -> None:
    if not chunks:
        return
    embeddings = embed_texts([c.text for c in chunks])
    store = get_vector_store()
    store.add(chunks, embeddings)
    store.save(DATA_DIR)
    document.num_chunks = len(chunks)

    registry = get_document_registry()
    registry.add(document)
    registry.save()


def ingest_pdf(file_bytes: bytes, filename: str) -> tuple[Document, list[Chunk]]:
    pages = parse_pdf(file_bytes)
    document = Document(id=str(uuid.uuid4()), title=filename, source_type=DocumentSourceType.pdf, source=filename)
    chunks = _build_chunks(document, pages)
    _embed_and_store(document, chunks)
    return document, chunks


def ingest_url(url: str) -> tuple[Document, list[Chunk]]:
    text = parse_url(url)
    document = Document(id=str(uuid.uuid4()), title=url, source_type=DocumentSourceType.url, source=url)
    chunks = _build_chunks(document, [(None, text)])
    _embed_and_store(document, chunks)
    return document, chunks


def ingest_text(text: str, title: str = "Untitled") -> tuple[Document, list[Chunk]]:
    parsed = parse_text(text)
    document = Document(id=str(uuid.uuid4()), title=title, source_type=DocumentSourceType.text, source=title)
    chunks = _build_chunks(document, [(None, parsed)])
    _embed_and_store(document, chunks)
    return document, chunks
