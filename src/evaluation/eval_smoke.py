import sys

from src.evaluation.metrics import ndcg_at_k


def run_smoke():
    ideal = [100, 80, 60, 40]
    pred = [80, 100, 40, 60]
    score = ndcg_at_k(pred, ideal, 3)
    if score > 0.8:
        print("Smoke test passed.")
        sys.exit(0)
    print("Smoke test failed.")
    sys.exit(1)


if __name__ == "__main__":
    run_smoke()
