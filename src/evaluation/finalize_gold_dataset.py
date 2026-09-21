import argparse
import json
from datetime import datetime, timezone

from src.evaluation.annotation_quality import validate_queue


def choose_gold_score(item: dict) -> tuple[float, str]:
    a_score = item.get("annotator_a_score")
    b_score = item.get("annotator_b_score")
    adjudicated = item.get("adjudicated_score")
    is_double = bool(item.get("double_annotation_required"))

    if a_score is None:
        raise ValueError(f"Missing annotator A score for {item['id']}")

    if not is_double:
        return float(a_score), "single_annotator"

    if b_score is None:
        raise ValueError(f"Missing annotator B score for double-annotated item {item['id']}")

    if adjudicated is not None:
        return float(adjudicated), "adjudication"

    if float(a_score) == float(b_score):
        return float(a_score), "double_annotator_consensus"

    raise ValueError(
        f"Double-annotation disagreement requires adjudication for {item['id']}"
    )


def build_gold(records: list[dict], dataset_version: str) -> list[dict]:
    validate_queue(records, require_complete=True)
    gold = []
    now = datetime.now(timezone.utc).isoformat()

    for item in records:
        score, source = choose_gold_score(item)
        output = {
            key: value
            for key, value in item.items()
            if not key.startswith("annotator_a_")
            and not key.startswith("annotator_b_")
            and key not in {"adjudicated_score", "adjudication_notes"}
        }
        output["expected_relevance"] = int(round(score))
        output["gold_score_source"] = source
        output["dataset_version"] = dataset_version
        output["gold_created_at"] = now
        gold.append(output)

    return gold


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a frozen J.A.R.V.I.S. gold ranking dataset.")
    parser.add_argument("--input", default="eval/annotation_queue.json")
    parser.add_argument("--output", default="eval/gold_dataset_v1.json")
    parser.add_argument("--version", default="real_news_v1")
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as handle:
        records = json.load(handle)

    gold = build_gold(records, args.version)
    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(gold, handle, indent=2, ensure_ascii=False)

    print(f"Created {len(gold)} gold records: {args.output}")


if __name__ == "__main__":
    main()