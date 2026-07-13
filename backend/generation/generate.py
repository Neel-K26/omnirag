from collections.abc import Iterator

from google.genai import types

from config import get_settings
from gemini_client import get_gemini_client
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
    {"prompt_tokens", "completion_tokens"} — Gemini reports cumulative usage on every chunk,
    so the holder just ends up holding whatever the last chunk reported."""
    settings = get_settings()
    client = get_gemini_client()
    context = _format_context(chunks)
    user_content = f"Source passages:\n\n{context}\n\nQuestion: {query}"

    stream = client.models.generate_content_stream(
        model=settings.gemini_model,
        contents=user_content,
        config=types.GenerateContentConfig(
            system_instruction=GENERATION_SYSTEM_PROMPT,
            temperature=0.2,
        ),
    )
    for chunk in stream:
        if usage_holder is not None and chunk.usage_metadata:
            usage_holder["prompt_tokens"] = chunk.usage_metadata.prompt_token_count
            usage_holder["completion_tokens"] = chunk.usage_metadata.candidates_token_count
        if chunk.text:
            yield chunk.text
