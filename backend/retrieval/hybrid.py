from ingestion.embeddings import embed_texts
from ingestion.store import get_vector_store
from models.schemas import Chunk, RetrievalStrategy
from retrieval.fusion import reciprocal_rank_fusion
from retrieval.reranker import rerank

DENSE_TOP_K = 20
SPARSE_TOP_K = 20
DEFAULT_TOP_K = 5


def dense_only(query: str, top_k: int = DEFAULT_TOP_K) -> list[tuple[Chunk, float]]:
    store = get_vector_store()
    query_embedding = embed_texts([query])[0]
    return store.search_dense(query_embedding, top_k=top_k)


def sparse_only(query: str, top_k: int = DEFAULT_TOP_K) -> list[tuple[Chunk, float]]:
    store = get_vector_store()
    return store.search_sparse(query, top_k=top_k)


def _fuse(query: str) -> list[tuple[Chunk, float]]:
    store = get_vector_store()
    query_embedding = embed_texts([query])[0]
    dense_chunks = [c for c, _ in store.search_dense(query_embedding, top_k=DENSE_TOP_K)]
    sparse_chunks = [c for c, _ in store.search_sparse(query, top_k=SPARSE_TOP_K)]
    return reciprocal_rank_fusion([dense_chunks, sparse_chunks])


def hybrid_fused(query: str, top_k: int = DEFAULT_TOP_K) -> list[tuple[Chunk, float]]:
    return _fuse(query)[:top_k]


def hybrid_rerank(query: str, top_k: int = DEFAULT_TOP_K) -> list[tuple[Chunk, float]]:
    fused_chunks = [c for c, _ in _fuse(query)]
    return rerank(query, fused_chunks, top_n=top_k)


_STRATEGY_FUNCS = {
    RetrievalStrategy.dense: dense_only,
    RetrievalStrategy.sparse: sparse_only,
    RetrievalStrategy.hybrid: hybrid_fused,
    RetrievalStrategy.hybrid_rerank: hybrid_rerank,
}


def retrieve(
    query: str,
    strategy: RetrievalStrategy = RetrievalStrategy.hybrid_rerank,
    top_k: int = DEFAULT_TOP_K,
) -> list[tuple[Chunk, float]]:
    return _STRATEGY_FUNCS[strategy](query, top_k)
