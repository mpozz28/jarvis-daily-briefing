from src.evaluation.metrics import (
    average_precision_at_k,
    mrr_at_k,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
)


def test_ranking_metrics():
    ideal = [100, 80, 60, 40]
    predicted = [80, 100, 40, 60]

    assert round(ndcg_at_k(predicted, ideal, 3), 4) == 0.9037
    assert precision_at_k([100, 20, 60], 3, 50) == 2 / 3
    assert recall_at_k([100, 20, 60], [100, 80, 60, 40], 3, 50) == 2 / 3
    assert mrr_at_k([20, 40, 100], 3, 50) == 1 / 3
    assert average_precision_at_k([100, 20, 60], 3, 50) == 5 / 6
