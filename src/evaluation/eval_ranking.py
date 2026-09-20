import json
import logging
import os
from datetime import datetime

from src.agents.ranking_agent import rank_and_filter
from src.agents.scoring_agent import score_and_filter_candidates
from src.evaluation.metrics import ndcg_at_k, precision_at_k, recall_at_k

logging.basicConfig(level=logging.INFO, format="%(asctime)s - EVALUATOR - %(message)s")
logger = logging.getLogger(__name__)

# FIX: Reference time fisso per garantire riproducibilità assoluta nel benchmark
REFERENCE_TIME = datetime.fromisoformat("2026-09-20T12:00:00+00:00")


def run_evaluation():
    logger.info("Avvio Benchmark (Input vs Deterministic vs Current)...")
    dataset_path = os.path.join(
        os.path.dirname(__file__), "../../eval/ranking_dataset.json"
    )

    with open(dataset_path, "r", encoding="utf-8") as f:
        golden_data = json.load(f)

    relevance_map = {item["id"]: item["expected_relevance"] for item in golden_data}
    ideal_order = sorted(
        golden_data, key=lambda x: x["expected_relevance"], reverse=True
    )
    ideal_relevances = [item["expected_relevance"] for item in ideal_order]

    test_data = []
    for item in golden_data:
        test_item = item.copy()
        test_item.pop("expected_relevance", None)
        test_data.append(test_item)

    # Baseline 0: Input Order (Come sono arrivati dall'ingestion)
    baseline_0_rel = [relevance_map.get(item["id"], 0) for item in test_data]

    # Baseline 1: Deterministic Scoring Only
    scored_data = score_and_filter_candidates(
        test_data.copy(), max_candidates=len(test_data), reference_time=REFERENCE_TIME
    )
    baseline_1_rel = [relevance_map.get(item["id"], 0) for item in scored_data]

    # Current: Deterministic + LLM Reranking
    ranked_data = rank_and_filter(
        test_data.copy(), max_items=20, reference_time=REFERENCE_TIME
    )
    current_rel = [relevance_map.get(item["id"], 0) for item in ranked_data]

    K_list = [3, 5]
    metrics = {"B0_Input": {}, "B1_Deterministic": {}, "Current_LLM": {}}
    systems = [
        ("B0_Input", baseline_0_rel),
        ("B1_Deterministic", baseline_1_rel),
        ("Current_LLM", current_rel),
    ]

    for k in K_list:
        for name, rels in systems:
            metrics[name][f"ndcg_{k}"] = ndcg_at_k(rels, ideal_relevances, k)
            metrics[name][f"p_{k}"] = precision_at_k(rels, k, 50)
            metrics[name][f"r_{k}"] = recall_at_k(rels, ideal_relevances, k, 50)

    logger.info("====================== BENCHMARK RESULTS ======================")
    logger.info("System           | NDCG@3 | NDCG@5 | P@3    | P@5    | R@5   ")
    logger.info("---------------------------------------------------------------")
    for name in ["B0_Input", "B1_Deterministic", "Current_LLM"]:
        m = metrics[name]
        logger.info(
            f"{name:<16} | {m['ndcg_3']:.4f} | {m['ndcg_5']:.4f} | {m['p_3']:.4f} | {m['p_5']:.4f} | {m['r_5']:.4f}"
        )
    logger.info("===============================================================")


if __name__ == "__main__":
    run_evaluation()
