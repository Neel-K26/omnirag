from collections.abc import Iterator

from config import get_settings
from groq_client import get_groq_client
from models.schemas import Chunk, Citation

# Positioned as a clinical literature assistant for V1; swap DOMAIN to retarget
# the same prompt structure for legal/enterprise/financial deployments.
DOMAIN = "clinical literature"

GENERATION_SYSTEM_PROMPT = f"""You are an AI assistant that answers questions about {DOMAIN} using only \
the provided source passages below.

Rules:
- Base your answer strictly on the provided passages. Do not use outside knowledge.
- Cite every claim inline using the passage number in brackets, e.g. [1], [2].
- If the passages do not contain enough information to answer, say so explicitly rather than guessing.
- Be concise and precise. This is not a substitute for professional medical advice."""


def _format_context(chunks: list[Chunk]) -> str:
    parts = []
    for i, c in enumerate(chunks, start=1):
        page_info = f", p.{c.metadata.page}" if c.metadata.page else ""
        parts.append(f"[{i}] ({c.metadata.document_title}{page_info}): {c.text}")
    return "\n\n".join(parts)


def build_citations(chunks: list[Chunk]) -> list[Citation]:
    return [
        Citation(index=i, document_title=c.metadata.document_title, page=c.metadata.page, text=c.text)
        for i, c in enumerate(chunks, start=1)
    ]


def stream_answer(query: str, chunks: list[Chunk], usage_holder: dict | None = None) -> Iterator[str]:
    """Streams the answer text. If usage_holder is passed, it is populated in-place with
    {"prompt_tokens", "completion_tokens"} once Groq reports usage (on the final chunk)."""
    settings = get_settings()
    client = get_groq_client()
    context = _format_context(chunks)
    messages = [
        {"role": "system", "content": GENERATION_SYSTEM_PROMPT},
        {"role": "user", "content": f"Source passages:\n\n{context}\n\nQuestion: {query}"},
    ]
    stream = client.chat.completions.create(
        model=settings.groq_model,
        messages=messages,
        temperature=0.2,
        stream=True,
    )
    for event in stream:
        if usage_holder is not None and event.usage:
            usage_holder["prompt_tokens"] = event.usage.prompt_tokens
            usage_holder["completion_tokens"] = event.usage.completion_tokens
        delta = event.choices[0].delta.content
        if delta:
            yield delta
