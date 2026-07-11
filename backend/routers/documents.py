from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from ingestion.pipeline import ingest_pdf, ingest_text, ingest_url
from ingestion.registry import get_document_registry
from models.schemas import Chunk, Document

router = APIRouter(prefix="/documents", tags=["documents"])


class IngestTextRequest(BaseModel):
    text: str
    title: str = "Untitled"


class IngestUrlRequest(BaseModel):
    url: str


class IngestResponse(BaseModel):
    document: Document
    chunks: list[Chunk]


@router.get("", response_model=list[Document])
def list_documents():
    return get_document_registry().list()


@router.post("/text", response_model=IngestResponse)
def upload_text(payload: IngestTextRequest):
    if not payload.text.strip():
        raise HTTPException(400, "text must not be empty")
    document, chunks = ingest_text(payload.text, title=payload.title)
    return IngestResponse(document=document, chunks=chunks)


@router.post("/url", response_model=IngestResponse)
def upload_url(payload: IngestUrlRequest):
    try:
        document, chunks = ingest_url(payload.url)
    except Exception as exc:
        raise HTTPException(502, f"Failed to fetch or parse URL: {exc}") from exc
    if document.num_chunks == 0:
        raise HTTPException(422, "No extractable text found at URL")
    return IngestResponse(document=document, chunks=chunks)


@router.post("/pdf", response_model=IngestResponse)
async def upload_pdf(file: UploadFile = File(...)):
    if not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(400, "file must be a PDF")
    file_bytes = await file.read()
    document, chunks = ingest_pdf(file_bytes, file.filename)
    if document.num_chunks == 0:
        raise HTTPException(422, "No extractable text found in PDF")
    return IngestResponse(document=document, chunks=chunks)
