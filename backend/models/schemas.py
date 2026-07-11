from enum import Enum
from typing import Optional

from pydantic import BaseModel


class DocumentSourceType(str, Enum):
    pdf = "pdf"
    url = "url"
    text = "text"


class ChunkMetadata(BaseModel):
    document_id: str
    document_title: str
    source_type: DocumentSourceType
    page: Optional[int] = None
    chunk_index: int


class Chunk(BaseModel):
    id: str
    text: str
    metadata: ChunkMetadata


class Document(BaseModel):
    id: str
    title: str
    source_type: DocumentSourceType
    source: str
    num_chunks: int = 0


class RetrievalStrategy(str, Enum):
    dense = "dense"
    sparse = "sparse"
    hybrid = "hybrid"
    hybrid_rerank = "hybrid_rerank"


class QueryIntent(str, Enum):
    factual = "factual"
    analytical = "analytical"
    comparative = "comparative"


class RoutingDecision(BaseModel):
    intent: QueryIntent
    strategy: RetrievalStrategy
    method: str  # "rule" or "prompt_fallback" — kept honest/visible, not hidden as "AI routing"


class SufficiencyResult(BaseModel):
    sufficient: bool
    reasoning: str
    reformulated_query: Optional[str] = None


class RetrievalHop(BaseModel):
    hop_number: int
    query: str
    strategy: RetrievalStrategy
    chunks: list[Chunk]
    sufficiency: SufficiencyResult


class AdaptiveRetrievalResult(BaseModel):
    routing: RoutingDecision
    hops: list[RetrievalHop]
    final_chunks: list[Chunk]


class Citation(BaseModel):
    index: int
    document_title: str
    page: Optional[int] = None
    text: str


class RagasScores(BaseModel):
    faithfulness: float
    answer_relevancy: float
    context_precision: float
