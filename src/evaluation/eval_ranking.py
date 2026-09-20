import argparse
import json
import logging
import os
from datetime import datetime, timezone

from src.agents.ranking_agent import rank_and_filter
from src.agents.scoring_agent import score_and_filter_candidates
from src.config import LLM_DEFAULT_MODEL
from src.evaluation.metrics import (
    average_precision_at_k,
    mrr_at_k,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - EVALUATOR - %(message)s")
logger = logging.getLogger("ranking-evaluator")

REFERENCE_TIME = datetime.fromisoformat("2026-09-20T12:00:00+00:00")
DEFAULT_K_LIST = (3, 5, 10)


def load_dataset(path: str) -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list) or not data:
        raise ValueError("Ranking dataset must be a non-empty JSON list.")

    required = {"id", "expected_relevance"}
    missing = required - set(data[0])
    if missing:
        raise ValueError(f"Dataset is missing required fields: {sorted(missing)}")

    return data


def profile_dataset(dataset: list[dict], threshold: int) -> dict:
    relevances = [int(item["expected_relevance"]) for item in dataset]
    relevant_count = sum(score >= threshold for score in relevances)
    stale_count = sum(
        str(item.get("published", "")).startswith(("2023-", "2024-", "2025-"))
        for item in dataset
    )

    return {
        "size": len(dataset),
        "relevance_threshold": threshold,
        "relevant_items": relevant_count,
        "relevant_rate": round(relevant_count / len(dataset), 4),
        "min_relevance": min(relevances),
        "max_relevance": max(relevances),
        "mean_relevance": round(sum(relevances) / len(relevances), 4),
        "stale_items_by_year_prefix": stale_count,
    }


def evaluate_ranked_relevances(
    name: str,
    predicted: list[int],
    ideal: list[int],
    k_list: tuple[int, ...],
    threshold: int,
) -> dict:
    metrics = {
        "system": name,
        "ndcg": {},
        "precision": {},
        "recall": {},
        "mrr": {},
        "average_precision": {},
    }

    for k in k_list:
        metrics["ndcg"][str(k)] = round(ndcg_at_k(predicted, ideal, k), 4)
        metrics["precision"][str(k)] = round(
            precision_at_k(predicted, k, threshold), 4
        )
        metrics["recall"][str(k)] = round(
            recall_at_k(predicted, ideal, k, threshold), 4
        )
        metrics["mrr"][str(k)] = round(mrr_at_k(predicted, k, threshold), 4)
        metrics["average_precision"][str(k)] = round(
            average_precision_at_k(predicted, ideal, k, threshold), 4
        )

    return metrics


def run_evaluation(
    dataset_path: str,
    include_llm: bool = False,
    threshold: int = 50,
    max_items: int = 20,
) -> dict:
    golden_data = load_dataset(dataset_path)
    test_data = [item.copy() for item in golden_data]

    relevance_map = {
        str(item["id"]): int(item["expected_relevance"]) for item in golden_data
    }
    ideal = sorted(
        (int(item["expected_relevance"]) for item in golden_data), reverse=True
    )

    input_order = [
        relevance_map[str(item["id"])]
        for item in test_data
    ]

    scored_data = score_and_filter_candidates(
        [item.copy() for item in test_data],
        max_candidates=len(test_data),
        reference_time=REFERENCE_TIME,
    )
    deterministic = [
        relevance_map[str(item["id"])]
        for item in scored_data
    ]

    systems = [
        evaluate_ranked_relevances(
            "input_order", input_order, ideal, DEFAULT_K_LIST, threshold
        ),
        evaluate_ranked_relevances(
            "deterministic", deterministic, ideal, DEFAULT_K_LIST, threshold
        ),
    ]

    if include_llm:
        ranked_data = rank_and_filter(
            [item.copy() for item in test_data],
            max_items=max_items,
            reference_time=REFERENCE_TIME,
        )
        llm_ranked = [
            relevance_map[str(item["id"])]
            for item in ranked_data
        ]
        systems.append(
            evaluate_ranked_relevances(
                "deterministic_plus_llm",
                llm_ranked,
                ideal,
                DEFAULT_K_LIST,
                threshold,
            )
        )

    result = {
        "benchmark": {
            "type": "single-list ranking regression",
            "dataset": os.path.relpath(dataset_path),
            "dataset_profile": profile_dataset(golden_data, threshold),
            "reference_time": REFERENCE_TIME.isoformat(),
            "llm_included": include_llm,
            "llm_model": LLM_DEFAULT_MODEL if include_llm else None,
            "max_items": max_items,
        },
        "systems": systems,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    logger.info("Ranking benchmark completed.")
    for system in systems:
        logger.info(
            "%s | NDCG@5=%s | P@5=%s | R@5=%s | MRR@5=%s",
            system["system"],
            system["ndcg"]["5"],
            system["precision"]["5"],
            system["recall"]["5"],
            system["mrr"]["5"],
        )

    return result


def main():
    parser = argparse.ArgumentParser(description="Evaluate J.A.R.V.I.S. ranking.")
    parser.add_argument(
        "--include-llm",
        action="store_true",
        help="Run the live LLM reranker. Disabled by default for reproducible CI.",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=50,
        help="Binary relevance threshold for Precision/Recall/MRR.",
    )
    parser.add_argument(
        "--dataset",
        default=os.path.join(
            os.path.dirname(__file__), "../../eval/ranking_dataset.json"
        ),
    )
    parser.add_argument(
        "--output",
        default=os.path.join(
            os.path.dirname(__file__), "../../eval/results/latest_ranking_eval.json"
        ),
    )
    args = parser.parse_args()

    result = run_evaluation(
        dataset_path=args.dataset,
        include_llm=args.include_llm,
        threshold=args.threshold,
    )

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
