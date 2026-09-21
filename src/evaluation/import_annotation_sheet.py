import argparse
import csv
import json


def parse_optional_score(value: str, field: str, required: bool = False):
    value = value.strip()
    if not value:
        if required:
            raise ValueError(f"Missing required {field}")
        return None
    score = float(value)
    if not 0 <= score <= 100:
        raise ValueError(f"{field} must be between 0 and 100")
    return int(score) if score.is_integer() else score


def main() -> None:
    parser = argparse.ArgumentParser(description="Import human annotations from an Excel-friendly CSV.")
    parser.add_argument("--input", default="eval/annotation_sheet_v1.csv")
    parser.add_argument("--queue", default="eval/annotation_queue.json")
    parser.add_argument("--output", default="eval/annotation_queue_annotated.json")
    args = parser.parse_args()

    with open(args.queue, "r", encoding="utf-8") as handle:
        queue = {str(item["id"]): item for item in json.load(handle)}

    with open(args.input, "r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))

    seen = set()
    for row in rows:
        item_id = str(row.get("id", ""))
        if item_id not in queue:
            raise ValueError(f"Unknown annotation id: {item_id}")
        if item_id in seen:
            raise ValueError(f"Duplicate annotation row: {item_id}")
        seen.add(item_id)
        item = queue[item_id]
        item["duplicate_group"] = row.get("duplicate_group") or None
        item["annotator_a_id"] = row.get("annotator_a_id") or None
        item["annotator_a_score"] = parse_optional_score(row.get("annotator_a_score", ""), "annotator_a_score")
        item["annotator_a_notes"] = row.get("annotator_a_notes", "")
        item["annotator_b_id"] = row.get("annotator_b_id") or None
        item["annotator_b_score"] = parse_optional_score(row.get("annotator_b_score", ""), "annotator_b_score")
        item["annotator_b_notes"] = row.get("annotator_b_notes", "")
        item["adjudicated_score"] = parse_optional_score(row.get("adjudicated_score", ""), "adjudicated_score")
        item["adjudication_notes"] = row.get("adjudication_notes", "")

    if seen != set(queue):
        missing = sorted(set(queue) - seen)
        raise ValueError(f"Missing annotation rows: {missing[:10]}")

    records = list(queue.values())
    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(records, handle, indent=2, ensure_ascii=False)
    print(f"Imported human annotations for {len(records)} records into {args.output}")


if __name__ == "__main__":
    main()