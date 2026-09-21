from src.evaluation.llm_annotation_agreement import build_report


def test_build_report_pairs_by_slot():
    assistance = {
        "suggestions": [
            {"id": "a", "slot": "A", "score": 80, "actual_model": "model-a", "rationale": "A"},
            {"id": "a", "slot": "B", "score": 65, "actual_model": "model-b", "rationale": "B"},
            {"id": "b", "slot": "A", "score": 90, "actual_model": "model-a", "rationale": "A"},
        ]
    }
    report = build_report(assistance, disagreement_threshold=10)
    assert report["items_with_both_models"] == 1
    assert report["disagreement_items"] == 1
    assert report["disagreements"][0]["absolute_difference"] == 15
