from src.evaluation.metrics import ndcg_at_k, precision_at_k


def test_ndcg_perfect_order():
    ideal = [100, 80, 50]
    pred = [100, 80, 50]
    assert ndcg_at_k(pred, ideal, 3) == 1.0


def test_precision():
    pred = [90, 80, 40, 30]
    assert precision_at_k(pred, 3, threshold=50) == 2 / 3
