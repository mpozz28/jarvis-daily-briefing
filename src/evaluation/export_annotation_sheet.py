import argparse
import csv
import json


def main() -> None:
    parser = argparse.ArgumentParser(description="Export annotation queue to an Excel-friendly CSV.")
    parser.add_argument("--input", default="eval/annotation_queue.json")
    parser.add_argument("--assistance", default="eval/annotation_assistance_v1.json")
    parser.add_argument("--output", default="eval/annotation_sheet_v1.csv")
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as handle:
        records = json.load(handle)

    assistance = {}
    try:
        with open(args.assistance, "r", encoding="utf-8") as handle:
            for suggestion in json.load(handle).get("suggestions", []):
                assistance.setdefault(suggestion["id"], []).append(suggestion)
    except FileNotFoundError:
        pass

    fields = [
        "id", "title", "summary", "area", "source", "published", "url",
        "split", "double_annotation_required", "duplicate_group",
        "llm_suggestion_a", "llm_rationale_a", "llm_suggestion_b", "llm_rationale_b",
        "annotator_a_id", "annotator_a_score", "annotator_a_notes",
        "annotator_b_id", "annotator_b_score", "annotator_b_notes",
        "adjudicated_score", "adjudication_notes",
    ]

    rows = []
    for item in records:
        suggestions = assistance.get(str(item["id"]), [])
        first = suggestions[0] if suggestions else {}
        second = suggestions[1] if len(suggestions) > 1 else {}
        rows.append({
            **{key: item.get(key) for key in fields if key in item},
            "llm_suggestion_a": first.get("score", ""),
            "llm_rationale_a": first.get("rationale", ""),
            "llm_suggestion_b": second.get("score", ""),
            "llm_rationale_b": second.get("rationale", ""),
        })

    with open(args.output, "w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    print(f"Exported {len(rows)} annotation rows to {args.output}")


if __name__ == "__main__":
    main()