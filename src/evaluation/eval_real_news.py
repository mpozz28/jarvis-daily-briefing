import argparse
import json
import os
from datetime import datetime, timezone

from src.agents.ranking_agent import rank_and_filter
from src.agents.scoring_agent import score_and_filter_candidates
from src.config import LLM_DEFAULT_MODEL
from src.evaluation.eval_ranking import evaluate_ranked_relevances, load_dataset, profile_dataset

DEFAULT_K_LIST = (3, 5, 10)

def parse_reference_time(dataset: list[dict], explicit: str | None) -> datetime:
    if explicit:
        value = datetime.fromisoformat(explicit.replace("Z", "+00:00"))
    else:
        published = []
        for item in dataset:
            try:
                value = datetime.fromisoformat(str(item["published"]).replace("Z", "+00:00"))
                if value.tzinfo is None:
                    value = value.replace(tzinfo=timezone.utc)
                published.append(value)
            except (KeyError, ValueError):
                continue
        if not published:
            raise ValueError("Cannot infer reference time from dataset")
        value = max(published)
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value

def validate_gold(dataset: list[dict]) -> None:
    required = {"id", "expected_relevance", "published", "title", "summary", "source"}
    for index, item in enumerate(dataset):
        missing = required - set(item)
        if missing:
            raise ValueError(f"Item {index} is missing required fields: {sorted(missing)}")
        score = item["expected_relevance"]
        if isinstance(score, bool) or not isinstance(score, (int, float)) or not 0 <= score <= 100:
            raise ValueError(f"Invalid expected_relevance for {item['id']}: {score}")

def run_real_evaluation(dataset_path: str, split: str, include_llm: bool, threshold: int, max_items: int, reference_time: str | None) -> dict:
    dataset = load_dataset(dataset_path)
    validate_gold(dataset)
    if split != "all":
        dataset = [item for item in dataset if item.get("split") == split]
    if not dataset:
        raise ValueError(f"No records found for split={split}")

    ref_time = parse_reference_time(dataset, reference_time)
    relevance_map = {str(item["id"]): int(item["expected_relevance"]) for item in dataset}
    ideal = sorted(relevance_map.values(), reverse=True)

    deterministic_data = score_and_filter_candidates(
        [item.copy() for item in dataset],
        max_candidates=len(dataset),
        reference_time=ref_time,
    )
    deterministic = [relevance_map[str(item["id"])] for item in deterministic_data]

    systems = [evaluate_ranked_relevances("input_order", [relevance_map[str(item["id"])] for item in dataset], ideal, DEFAULT_K_LIST, threshold),
               evaluate_ranked_relevances("deterministic", deterministic, ideal, DEFAULT_K_LIST, threshold)]

    if include_llm:
        ranked = rank_and_filter([item.copy() for item in dataset], max_items=max_items, reference_time=ref_time)
        llm_ranked = [relevance_map[str(item["id"])] for item in ranked]
        systems.append(evaluate_ranked_relevances("deterministic_plus_llm", llm_ranked, ideal, DEFAULT_K_LIST, threshold))

    return {
        "benchmark": {
            "type": "real-news temporal ranking evaluation",
            "dataset": os.path.relpath(dataset_path),
            "split": split,
            "dataset_profile": profile_dataset(dataset, threshold),
            "reference_time": ref_time.isoformat(),
            "llm_included": include_llm,
            "llm_model": LLM_DEFAULT_MODEL if include_llm else None,
            "max_items": max_items,
            "gold_warning": "Gold labels must come from the documented annotation workflow; LLM suggestions alone are not gold.",
        },
        "systems": systems,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate J.A.R.V.I.S. on the frozen real-news gold dataset.")
    parser.add_argument("--dataset", default="eval/gold_dataset_v1.json")
    parser.add_argument("--split", choices=["dev", "test", "all"], default="test")
    parser.add_argument("--include-llm", action="store_true")
    parser.add_argument("--threshold", type=int, default=50)
    parser.add_argument("--max-items", type=int, default=20)
    parser.add_argument("--reference-time", default=None, help="ISO-8601 reference time. If omitted, use latest article timestamp in the selected split.")
    parser.add_argument("--output", default="eval/results/real_news_test.json")
    args = parser.parse_args()
    result = run_real_evaluation(args.dataset, args.split, args.include_llm, args.threshold, args.max_items, args.reference_time)
    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, ensure_ascii=False)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()