from functools import lru_cache

from langchain_groq import ChatGroq
from ragas import EvaluationDataset, SingleTurnSample, evaluate
from ragas.embeddings.base import BaseRagasEmbeddings
from ragas.llms import LangchainLLMWrapper
from ragas.metrics import LLMContextPrecisionWithoutReference, answer_relevancy, faithfulness
from ragas.run_config import RunConfig

from config import get_settings
from ingestion.embeddings import embed_texts
from models.schemas import RagasScores

CONTEXT_PRECISION = LLMContextPrecisionWithoutReference()
METRICS = [faithfulness, answer_relevancy, CONTEXT_PRECISION]


class _SentenceTransformerRagasEmbeddings(BaseRagasEmbeddings):
    """Reuses the already-loaded sentence-transformers singleton (ingestion.embeddings)
    instead of loading a second copy of the model via langchain_huggingface."""

    def __init__(self):
        super().__init__()
        self.set_run_config(RunConfig())

    def embed_query(self, text: str) -> list[float]:
        return embed_texts([text])[0].tolist()

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return embed_texts(texts).tolist()

    async def aembed_query(self, text: str) -> list[float]:
        return self.embed_query(text)

    async def aembed_documents(self, texts: list[str]) -> list[list[float]]:
        return self.embed_documents(texts)


@lru_cache
def get_ragas_llm() -> LangchainLLMWrapper:
    settings = get_settings()
    chat = ChatGroq(model=settings.groq_model, api_key=settings.groq_api_key, temperature=0)
    return LangchainLLMWrapper(chat)


@lru_cache
def get_ragas_embeddings() -> _SentenceTransformerRagasEmbeddings:
    return _SentenceTransformerRagasEmbeddings()


def _row_to_scores(row) -> RagasScores:
    return RagasScores(
        faithfulness=float(row["faithfulness"]),
        answer_relevancy=float(row["answer_relevancy"]),
        context_precision=float(row[CONTEXT_PRECISION.name]),
    )


def evaluate_response(query: str, response: str, contexts: list[str]) -> RagasScores:
    """Real-time, per-query RAGAS scoring for a single chat turn."""
    per_query, _ = evaluate_batch([(query, response, contexts)])
    return per_query[0]


def evaluate_batch(samples: list[tuple[str, str, list[str]]]) -> tuple[list[RagasScores], RagasScores]:
    """Batch RAGAS scoring (e.g. the benchmark runner's preset queries).
    Returns (per-query scores, aggregate/mean scores)."""
    eval_samples = [
        SingleTurnSample(user_input=query, response=response, retrieved_contexts=contexts)
        for query, response, contexts in samples
    ]
    dataset = EvaluationDataset(samples=eval_samples)
    result = evaluate(
        dataset=dataset,
        metrics=METRICS,
        llm=get_ragas_llm(),
        embeddings=get_ragas_embeddings(),
        show_progress=False,
        raise_exceptions=False,
    )
    df = result.to_pandas()

    per_query = [_row_to_scores(row) for _, row in df.iterrows()]
    aggregate = RagasScores(
        faithfulness=float(df["faithfulness"].mean()),
        answer_relevancy=float(df["answer_relevancy"].mean()),
        context_precision=float(df[CONTEXT_PRECISION.name].mean()),
    )
    return per_query, aggregate
