# Groq on-demand pricing, USD per 1M tokens. Source: https://groq.com/pricing (checked 2026-07).
# Estimates only — actual billing may differ (batching/caching discounts, price changes).
GROQ_PRICING_PER_MILLION_TOKENS = {
    "llama-3.3-70b-versatile": {"input": 0.59, "output": 0.79},
    "llama-3.1-8b-instant": {"input": 0.05, "output": 0.08},
}


def estimate_cost_usd(model: str, prompt_tokens: int, completion_tokens: int) -> float | None:
    rates = GROQ_PRICING_PER_MILLION_TOKENS.get(model)
    if rates is None:
        return None
    return (prompt_tokens * rates["input"] + completion_tokens * rates["output"]) / 1_000_000
