import argparse
import json
import random
from collections import Counter, defaultdict
from pathlib import Path


def load_corpus(path: str) -> list[dict]:
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, list) or not data:
        raise ValueError("Corpus must be a non-empty JSON list.")
    return data


def stratified_double_sample(corpus: list[dict], fraction: float, seed: int) -> set[str]:
    if not 0 < fraction <= 1:
        raise ValueError("Double-annotation fraction must be in (0, 1].")

    rng = random.Random(seed)
    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for item in corpus:
        groups[(item.get("split", "unknown"), item.get("area", "OTHER"))].append(item)

    target = max(1, round(len(corpus) * fraction))
    selected: list[dict] = []

    for key in sorted(groups):
        if len(selected) >= target:
            break
        candidates = groups[key][:]
        rng.shuffle(candidates)
        selected.append(candidates[0])

    selected_ids = {str(item["id"]) for item in selected}
    remaining = [item for item in corpus if str(item["id"]) not in selected_ids]
    rng.shuffle(remaining)

    for item in remaining:
        if len(selected) >= target:
            break
        selected.append(item)

    return {str(item["id"]) for item in selected}


def prepare_queue(corpus: list[dict], double_fraction: float, seed: int) -> tuple[list[dict], list[dict], dict]:
    double_ids = stratified_double_sample(corpus, double_fraction, seed)
    queue = []

    for item in corpus:
        record = {
            "id": str(item["id"]),
            "title": item.get("title", ""),
            "summary": item.get("summary", ""),
            "area": item.get("area", "OTHER"),
            "source": item.get("source", ""),
            "domain": item.get("domain", ""),
            "published": item.get("published", ""),
            "url": item.get("url", ""),
            "canonical_url": item.get("canonical_url", ""),
            "duplicate_group": item.get("duplicate_group"),
            "split": item.get("split"),
            "annotation_version": "v1.0",
            "double_annotation_required": str(item["id"]) in double_ids,
            "annotator_a_id": None,
            "annotator_a_score": None,
            "annotator_a_notes": "",
            "annotator_b_id": None,
            "annotator_b_score": None,
            "annotator_b_notes": "",
            "adjudicated_score": None,
            "adjudication_notes": "",
        }
        queue.append(record)

    rng = random.Random(seed)
    rng.shuffle(queue)
    double_queue = [item for item in queue if item["double_annotation_required"]]

    manifest = {
        "dataset_type": "real_news_annotation_queue",
        "annotation_version": "v1.0",
        "seed": seed,
        "items": len(queue),
        "double_annotation_fraction": double_fraction,
        "double_annotation_target": len(double_queue),
        "split_counts": dict(Counter(item.get("split") for item in queue)),
        "area_counts": dict(Counter(item.get("area") for item in queue)),
        "double_split_counts": dict(Counter(item.get("split") for item in double_queue)),
        "double_area_counts": dict(Counter(item.get("area") for item in double_queue)),
        "gold_status": "unannotated",
    }
    return queue, double_queue, manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare a stratified annotation queue from the real J.A.R.V.I.S. corpus.")
    parser.add_argument("--input", default="eval/real_corpus_unannotated.json")
    parser.add_argument("--output", default="eval/annotation_queue.json")
    parser.add_argument("--double-output", default="eval/double_annotation_sample.json")
    parser.add_argument("--manifest", default="eval/annotation_manifest.json")
    parser.add_argument("--double-fraction", type=float, default=0.20)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    corpus = load_corpus(args.input)
    queue, double_queue, manifest = prepare_queue(corpus, args.double_fraction, args.seed)

    for output in (args.output, args.double_output, args.manifest):
        Path(output).parent.mkdir(parents=True, exist_ok=True)

    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(queue, handle, indent=2, ensure_ascii=False)
    with open(args.double_output, "w", encoding="utf-8") as handle:
        json.dump(double_queue, handle, indent=2, ensure_ascii=False)
    with open(args.manifest, "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2, ensure_ascii=False)

    print(f"Prepared {len(queue)} annotation records; {len(double_queue)} require double annotation.")


if __name__ == "__main__":
    main()
