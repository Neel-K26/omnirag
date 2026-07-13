# Gemini API on-demand pricing, USD per 1M tokens. Source: web pricing aggregators
# (checked 2026-07); Google doesn't publish per-alias prices, so this is priced as
# whatever "gemini-flash-lite-latest" currently resolves to (confirmed via
# response.model_version): gemini-3.1-flash-lite. If Google repoints the alias to a
# different underlying model, update this entry to match.
# Estimates only — actual billing may differ (batching/caching discounts, price changes).
GEMINI_PRICING_PER_MILLION_TOKENS = {
    "gemini-flash-lite-latest": {"input": 0.25, "output": 1.50},
}


def estimate_cost_usd(model: str, prompt_tokens: int, completion_tokens: int) -> float | None:
    rates = GEMINI_PRICING_PER_MILLION_TOKENS.get(model)
    if rates is None:
        return None
    return (prompt_tokens * rates["input"] + completion_tokens * rates["output"]) / 1_000_000
