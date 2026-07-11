import pickle
import re
from functools import lru_cache
from pathlib import Path

import faiss
import numpy as np
from rank_bm25 import BM25Okapi

from models.schemas import Chunk

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "index"

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def simple_tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


class VectorStore:
    def __init__(self, dim: int):
        self.dim = dim
        self.index = faiss.IndexFlatIP(dim)
        self.chunks: list[Chunk] = []
        self._tokenized_corpus: list[list[str]] = []
        self._bm25: BM25Okapi | None = None

    @property
    def size(self) -> int:
        return len(self.chunks)

    def add(self, chunks: list[Chunk], embeddings: np.ndarray) -> None:
        if len(chunks) != embeddings.shape[0]:
            raise ValueError("chunks and embeddings length mismatch")
        normalized = embeddings.astype("float32").copy()
        faiss.normalize_L2(normalized)
        self.index.add(normalized)
        self.chunks.extend(chunks)
        self._tokenized_corpus.extend(simple_tokenize(c.text) for c in chunks)
        self._bm25 = BM25Okapi(self._tokenized_corpus)

    def search_dense(self, query_embedding: np.ndarray, top_k: int = 20) -> list[tuple[Chunk, float]]:
        if self.size == 0:
            return []
        query = query_embedding.reshape(1, -1).astype("float32").copy()
        faiss.normalize_L2(query)
        k = min(top_k, self.size)
        scores, indices = self.index.search(query, k)
        return [(self.chunks[i], float(s)) for s, i in zip(scores[0], indices[0]) if i != -1]

    def search_sparse(self, query: str, top_k: int = 20) -> list[tuple[Chunk, float]]:
        if self._bm25 is None:
            return []
        scores = self._bm25.get_scores(simple_tokenize(query))
        k = min(top_k, self.size)
        top_idx = np.argsort(scores)[::-1][:k]
        return [(self.chunks[i], float(scores[i])) for i in top_idx]

    def save(self, index_dir: Path = DATA_DIR) -> None:
        index_dir.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(index_dir / "faiss.index"))
        with open(index_dir / "store.pkl", "wb") as f:
            pickle.dump({"chunks": self.chunks, "tokenized_corpus": self._tokenized_corpus}, f)

    @classmethod
    def load(cls, index_dir: Path = DATA_DIR, dim: int = 384) -> "VectorStore":
        store = cls(dim)
        faiss_path = index_dir / "faiss.index"
        pkl_path = index_dir / "store.pkl"
        if faiss_path.exists() and pkl_path.exists():
            store.index = faiss.read_index(str(faiss_path))
            with open(pkl_path, "rb") as f:
                data = pickle.load(f)
            store.chunks = data["chunks"]
            store._tokenized_corpus = data["tokenized_corpus"]
            store._bm25 = BM25Okapi(store._tokenized_corpus) if store._tokenized_corpus else None
        return store


@lru_cache
def get_vector_store() -> VectorStore:
    from ingestion.embeddings import get_embedding_dim

    return VectorStore.load(DATA_DIR, get_embedding_dim())
