import asyncio
from functools import lru_cache

from google.genai import types
from langchain_core.outputs import Generation, LLMResult
from langchain_core.prompt_values import PromptValue
from ragas import EvaluationDataset, SingleTurnSample, evaluate
from ragas.embeddings.base import BaseRagasEmbeddings
from ragas.llms.base import BaseRagasLLM
from ragas.metrics import LLMContextPrecisionWithoutReference, answer_relevancy, faithfulness
from ragas.run_config import RunConfig

from config import get_settings
from gemini_client import get_gemini_client
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


class _GeminiRagasLLM(BaseRagasLLM):
    """Implements ragas's own BaseRagasLLM interface directly against the google-genai SDK,
    bypassing langchain-google-genai entirely (same pattern as the embeddings wrapper above).

    Every langchain-google-genai version compatible with our pinned pre-1.0 langchain-core
    (required by ragas==0.2.15) depends on the legacy google-ai-generativelanguage client,
    which rejects this project's API key outright (confirmed via direct testing — both gRPC
    and REST transports fail). Every version using the working google-genai SDK requires
    langchain-core>=1.0, which breaks ragas's own imports. There is no version satisfying both."""

    def __init__(self, model: str):
        super().__init__()
        self.model = model
        self.set_run_config(RunConfig())

    def is_finished(self, response: LLMResult) -> bool:
        # Judge prompts are short and bounded; skip ragas's default per-call warning log
        # for a finish-reason check we don't track.
        return True

    def _generate_one(self, prompt_text: str, temperature: float) -> str:
        client = get_gemini_client()
        response = client.models.generate_content(
            model=self.model,
            contents=prompt_text,
            config=types.GenerateContentConfig(temperature=temperature),
        )
        return response.text or ""

    async def _agenerate_one(self, prompt_text: str, temperature: float) -> str:
        client = get_gemini_client()
        response = await client.aio.models.generate_content(
            model=self.model,
            contents=prompt_text,
            config=types.GenerateContentConfig(temperature=temperature),
        )
        return response.text or ""

    def generate_text(
        self,
        prompt: PromptValue,
        n: int = 1,
        temperature: float | None = None,
        stop: list[str] | None = None,
        callbacks=None,
    ) -> LLMResult:
        if temperature is None:
            temperature = self.get_temperature(n)
        prompt_text = prompt.to_string()
        generations = [Generation(text=self._generate_one(prompt_text, temperature)) for _ in range(n)]
        return LLMResult(generations=[generations])

    async def agenerate_text(
        self,
        prompt: PromptValue,
        n: int = 1,
        temperature: float | None = None,
        stop: list[str] | None = None,
        callbacks=None,
    ) -> LLMResult:
        if temperature is None:
            temperature = self.get_temperature(n)
        prompt_text = prompt.to_string()
        texts = await asyncio.gather(*(self._agenerate_one(prompt_text, temperature) for _ in range(n)))
        generations = [Generation(text=t) for t in texts]
        return LLMResult(generations=[generations])


@lru_cache
def get_ragas_llm() -> _GeminiRagasLLM:
    settings = get_settings()
    return _GeminiRagasLLM(model=settings.gemini_model)


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
