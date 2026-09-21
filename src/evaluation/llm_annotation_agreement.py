import argparse
import csv
import json
import os


def build_report(assistance: dict, disagreement_threshold: float = 10.0) -> dict:
    by_id = {}
    for item in assistance.get("suggestions", []):
        by_id.setdefault(str(item["id"]), {})[item.get("slot", "A")] = item

    pairs = []
    disagreements = []
    for item_id, slots in by_id.items():
        a = slots.get("A")
        b = slots.get("B")
        if not a or not b:
            continue
        diff = abs(float(a["score"]) - float(b["score"]))
        pair = {
            "id": item_id,
            "score_a": float(a["score"]),
            "score_b": float(b["score"]),
            "absolute_difference": diff,
            "actual_model_a": a.get("actual_model"),
            "actual_model_b": b.get("actual_model"),
            "rationale_a": a.get("rationale", ""),
            "rationale_b": b.get("rationale", ""),
        }
        pairs.append(pair)
        if diff > disagreement_threshold:
            disagreements.append(pair)

    diffs = [p["absolute_difference"] for p in pairs]
    return {
        "items_with_both_models": len(pairs),
        "exact_agreement_rate": sum(d == 0 for d in diffs) / len(diffs) if diffs else None,
        "within_5_points_rate": sum(d <= 5 for d in diffs) / len(diffs) if diffs else None,
        "within_10_points_rate": sum(d <= 10 for d in diffs) / len(diffs) if diffs else None,
        "mean_absolute_difference": sum(diffs) / len(diffs) if diffs else None,
        "disagreement_threshold": disagreement_threshold,
        "disagreement_items": len(disagreements),
        "disagreements": sorted(
            disagreements,
            key=lambda x: x["absolute_difference"],
            reverse=True,
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare A/B LLM annotation suggestions.")
    parser.add_argument("--input", default="eval/annotation_assistance_v1.json")
    parser.add_argument("--output", default="eval/llm_annotation_agreement_v1.json")
    parser.add_argument("--review-csv", default="eval/human_review_queue_v1.csv")
    parser.add_argument("--threshold", type=float, default=10.0)
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as handle:
        assistance = json.load(handle)

    report = build_report(assistance, args.threshold)
    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)

    with open(args.review_csv, "w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "id",
                "score_a",
                "score_b",
                "absolute_difference",
                "actual_model_a",
                "actual_model_b",
                "rationale_a",
                "rationale_b",
                "human_score",
                "human_notes",
            ],
        )
        writer.writeheader()
        for row in report["disagreements"]:
            writer.writerow({**row, "human_score": "", "human_notes": ""})

    print(json.dumps(
        {
            key: report[key]
            for key in [
                "items_with_both_models",
                "exact_agreement_rate",
                "within_5_points_rate",
                "within_10_points_rate",
                "mean_absolute_difference",
                "disagreement_items",
            ]
        },
        indent=2,
    ))


if __name__ == "__main__":
    main()
