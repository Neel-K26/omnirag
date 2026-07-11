import json

from groq_client import get_groq_client
from models.schemas import Chunk, SufficiencyResult

# Narrow judgment task — a fast/cheap model is enough; generation uses the larger model.
SUFFICIENCY_MODEL = "llama-3.1-8b-instant"

SUFFICIENCY_SYSTEM_PROMPT = (
    "You are evaluating whether retrieved context passages contain enough information "
    "to answer a user's question. Respond with a JSON object with exactly these fields:\n"
    '{"sufficient": true or false, "reasoning": "one sentence explanation", '
    '"reformulated_query": "a better search query to fill the gap, or null if sufficient"}\n'
    "Be strict: if the passages only partially address the question or are off-topic, "
    "mark sufficient as false."
)


def check_sufficiency(query: str, chunks: list[Chunk]) -> SufficiencyResult:
    if not chunks:
        return SufficiencyResult(sufficient=False, reasoning="No chunks retrieved.", reformulated_query=query)

    context = "\n\n".join(f"[{i}] {c.text}" for i, c in enumerate(chunks, start=1))
    user_content = f"Question: {query}\n\nRetrieved passages:\n{context}"

    client = get_groq_client()
    response = client.chat.completions.create(
        model=SUFFICIENCY_MODEL,
        messages=[
            {"role": "system", "content": SUFFICIENCY_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        temperature=0,
        max_tokens=200,
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content or "{}"
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return SufficiencyResult(
            sufficient=True,
            reasoning="Could not parse sufficiency response; defaulting to sufficient.",
            reformulated_query=None,
        )

    return SufficiencyResult(
        sufficient=bool(data.get("sufficient", True)),
        reasoning=str(data.get("reasoning", "")),
        reformulated_query=data.get("reformulated_query") or None,
    )
