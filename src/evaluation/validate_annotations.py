import argparse
import json

from src.evaluation.annotation_quality import agreement_report, validate_queue


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate a J.A.R.V.I.S. annotation queue.")
    parser.add_argument("--input", default="eval/annotation_queue.json")
    parser.add_argument("--require-complete", action="store_true")
    parser.add_argument("--output", default="eval/annotation_quality_report.json")
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as handle:
        records = json.load(handle)

    validation = validate_queue(records, require_complete=args.require_complete)
    report = {
        **validation,
        "agreement": agreement_report(records),
        "input": args.input,
    }

    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()