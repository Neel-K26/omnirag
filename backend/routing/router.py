from google.genai import types

from config import get_settings
from gemini_client import get_gemini_client
from models.schemas import QueryIntent, RetrievalStrategy, RoutingDecision

COMPARATIVE_KEYWORDS = [
    "compare",
    "comparison",
    "versus",
    " vs ",
    " vs.",
    "difference between",
    "differences between",
    "better than",
    "compared to",
    "which is better",
    "pros and cons",
]

ANALYTICAL_KEYWORDS = [
    "why",
    "how does",
    "how do",
    "explain",
    "analyze",
    "analysis",
    "what causes",
    "relationship between",
    "impact of",
    "effect of",
    "mechanism of",
]

FACTUAL_KEYWORDS = [
    "what is",
    "what are",
    "define",
    "definition",
    "when did",
    "when is",
    "who is",
    "how many",
    "how much",
    "list the",
    "name the",
]

# factual -> hybrid+rerank, analytical -> dense only, comparative -> sparse+dense (fused, no rerank)
INTENT_STRATEGY_MAP: dict[QueryIntent, RetrievalStrategy] = {
    QueryIntent.factual: RetrievalStrategy.hybrid_rerank,
    QueryIntent.analytical: RetrievalStrategy.dense,
    QueryIntent.comparative: RetrievalStrategy.hybrid,
}

CLASSIFY_SYSTEM_PROMPT = (
    "You are a query intent classifier for a retrieval-augmented search system. "
    "Classify the user's query into exactly one of three categories:\n"
    "- factual: seeks a specific fact, definition, or direct lookup\n"
    "- analytical: asks why or how something happens, seeks explanation or reasoning\n"
    "- comparative: asks to compare, contrast, or weigh two or more things\n"
    "Respond with only one word: factual, analytical, or comparative."
)


def classify_rule_based(query: str) -> QueryIntent | None:
    padded = f" {query.lower().strip()} "
    if any(kw in padded for kw in COMPARATIVE_KEYWORDS):
        return QueryIntent.comparative
    if any(kw in padded for kw in ANALYTICAL_KEYWORDS):
        return QueryIntent.analytical
    if any(kw in padded for kw in FACTUAL_KEYWORDS):
        return QueryIntent.factual
    return None


def classify_prompt_based(query: str) -> QueryIntent:
    settings = get_settings()
    client = get_gemini_client()
    response = client.models.generate_content(
        model=settings.gemini_model,
        contents=query,
        config=types.GenerateContentConfig(
            system_instruction=CLASSIFY_SYSTEM_PROMPT,
            temperature=0,
            max_output_tokens=5,
        ),
    )
    label = (response.text or "").strip().lower()
    try:
        return QueryIntent(label)
    except ValueError:
        return QueryIntent.factual


def route_query(query: str) -> RoutingDecision:
    intent = classify_rule_based(query)
    method = "rule"
    if intent is None:
        intent = classify_prompt_based(query)
        method = "prompt_fallback"
    return RoutingDecision(intent=intent, strategy=INTENT_STRATEGY_MAP[intent], method=method)
