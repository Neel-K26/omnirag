from evaluation.ragas_eval import evaluate_batch, evaluate_response

HYPERTENSION_CONTEXT = (
    "Hypertension is a chronic condition in which blood pressure in the arteries is "
    "persistently elevated, typically defined as 130/80 mmHg or higher. It is a major "
    "risk factor for cardiovascular disease including stroke and heart failure."
)


def test_evaluate_response_grounded_answer_scores_high():
    scores = evaluate_response(
        query="What is hypertension?",
        response="Hypertension is persistently elevated blood pressure and a major risk factor for stroke and heart failure.",
        contexts=[HYPERTENSION_CONTEXT],
    )
    assert scores.faithfulness > 0.8
    assert scores.answer_relevancy > 0.8
    assert scores.context_precision > 0.8


def test_evaluate_response_unfaithful_answer_scores_low_faithfulness():
    scores = evaluate_response(
        query="What is hypertension?",
        response="Hypertension is a rare genetic disorder that only affects children under age 5 and is caused by a virus.",
        contexts=[HYPERTENSION_CONTEXT],
    )
    assert scores.faithfulness < 0.3


def test_evaluate_batch_returns_per_query_and_aggregate():
    samples = [
        (
            "What is hypertension?",
            "Hypertension is persistently elevated blood pressure, a major risk factor for stroke and heart failure.",
            [HYPERTENSION_CONTEXT],
        ),
        (
            "What medications treat type 2 diabetes?",
            "Metformin is typically the first-line medication for type 2 diabetes.",
            [
                "Metformin is typically the first-line medication due to its efficacy, "
                "safety profile, and low cost."
            ],
        ),
    ]
    per_query, aggregate = evaluate_batch(samples)

    assert len(per_query) == 2
    for scores in per_query:
        assert 0.0 <= scores.faithfulness <= 1.0
        assert 0.0 <= scores.answer_relevancy <= 1.0
        assert 0.0 <= scores.context_precision <= 1.0

    assert aggregate.faithfulness == (per_query[0].faithfulness + per_query[1].faithfulness) / 2
