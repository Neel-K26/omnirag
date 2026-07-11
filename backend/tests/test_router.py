from models.schemas import QueryIntent, RetrievalStrategy
from routing.router import INTENT_STRATEGY_MAP, classify_rule_based, route_query


def test_rule_based_factual():
    assert classify_rule_based("What is hypertension?") == QueryIntent.factual
    assert classify_rule_based("Define insulin resistance") == QueryIntent.factual
    assert classify_rule_based("How many people have type 2 diabetes?") == QueryIntent.factual


def test_rule_based_analytical():
    assert classify_rule_based("Why does insulin resistance develop in type 2 diabetes?") == QueryIntent.analytical
    assert classify_rule_based("Explain the mechanism of ACE inhibitors") == QueryIntent.analytical
    assert classify_rule_based("What is the impact of sodium intake on blood pressure?") == QueryIntent.analytical


def test_rule_based_comparative():
    assert classify_rule_based("Compare hypertension and diabetes treatment approaches") == QueryIntent.comparative
    assert classify_rule_based("ACE inhibitors vs calcium channel blockers") == QueryIntent.comparative
    assert classify_rule_based("What is the difference between type 1 and type 2 diabetes?") == QueryIntent.comparative


def test_rule_based_returns_none_when_no_keyword_matches():
    assert classify_rule_based("Metformin dosage adjustments in elderly patients with renal impairment") is None


def test_intent_strategy_map_covers_every_intent():
    for intent in QueryIntent:
        assert intent in INTENT_STRATEGY_MAP

    assert INTENT_STRATEGY_MAP[QueryIntent.factual] == RetrievalStrategy.hybrid_rerank
    assert INTENT_STRATEGY_MAP[QueryIntent.analytical] == RetrievalStrategy.dense
    assert INTENT_STRATEGY_MAP[QueryIntent.comparative] == RetrievalStrategy.hybrid


def test_route_query_rule_based_path_reports_method():
    decision = route_query("What is hypertension?")
    assert decision.intent == QueryIntent.factual
    assert decision.strategy == RetrievalStrategy.hybrid_rerank
    assert decision.method == "rule"


def test_route_query_falls_back_to_prompt_when_ambiguous():
    decision = route_query("Blood pressure normal range for healthy adults")
    assert decision.method == "prompt_fallback"
    assert decision.intent in QueryIntent
    assert decision.strategy == INTENT_STRATEGY_MAP[decision.intent]
