import argparse
import json
import os
from datetime import datetime, timezone

from src.config import LLM_DEFAULT_MODEL, LLM_FALLBACK_MODELS
from src.llm_router import LLMFallbackRouter

SCORING_SYSTEM_PROMPT = '''You are assisting with annotation of a news-ranking evaluation dataset.
Assign an informational relevance score from 0 to 100 for a general daily intelligence briefing.

Judge ONLY the article's information value using impact, novelty, breadth and briefing value.
Do not reward publisher prestige or sensational wording.
Do not make political recommendations or assess political choices.
Return ONLY valid JSON matching:
{"id":"...","score":0,"rationale":"short explanation","flags":[]}
flags may include: stale, duplicate_candidate, ambiguous_area, low_information, high_impact.
'''

def build_prompt(items: list[dict]) -> str:
    payload = []
    for item in items:
        payload.append({
            "id": str(item["id"]),
            "title": item.get("title", ""),
            "summary": item.get("summary", ""),
            "area": item.get("area", "OTHER"),
            "source": item.get("source", ""),
            "published": item.get("published", ""),
        })
    return (
        "Score each article independently. Return a JSON array with one object per input id. "
        "Keep scores between 0 and 100.\n\n"
        + json.dumps(payload, ensure_ascii=False)
    )

def parse_response(raw: str, expected_ids: set[str]) -> dict[str, dict]:
    text = raw.strip()
    if text.startswith("```"):
        text = text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    decoder = json.JSONDecoder()
    objects = []
    cursor = 0
    while cursor < len(text):
        while cursor < len(text) and text[cursor].isspace():
            cursor += 1
        if cursor >= len(text):
            break
        obj, end = decoder.raw_decode(text, cursor)
        objects.append(obj)
        cursor = end

    if len(objects) == 1 and isinstance(objects[0], list):
        data = objects[0]
    else:
        data = []
        for obj in objects:
            if isinstance(obj, list):
                data.extend(obj)
            else:
                data.append(obj)

    if not isinstance(data, list):
        raise ValueError("LLM response must contain a JSON array or JSON objects")
    parsed = {}
    for obj in data:
        if not isinstance(obj, dict):
            raise ValueError("Every LLM annotation must be an object")
        item_id = str(obj.get("id", ""))
        if item_id not in expected_ids:
            raise ValueError(f"Unexpected annotation id: {item_id}")
        score = obj.get("score")
        if isinstance(score, bool) or not isinstance(score, (int, float)) or not 0 <= score <= 100:
            raise ValueError(f"Invalid score for {item_id}: {score}")
        parsed[item_id] = {
            "score": float(score),
            "rationale": str(obj.get("rationale", "")).strip(),
            "flags": obj.get("flags", []),
        }
    missing = expected_ids - set(parsed)
    if missing:
        raise ValueError(f"Missing annotations for ids: {sorted(missing)}")
    return parsed

def annotate_queue(records: list[dict], batch_size: int, model_a: str, model_b: str | None, limit: int | None) -> dict:
    selected = records[:limit] if limit else records
    router = LLMFallbackRouter(temperature=0.0)
    suggestions = []

    for start in range(0, len(selected), batch_size):
        batch = selected[start:start + batch_size]
        parsed = parse_response(
            router.invoke_with_metadata(build_prompt(batch), system_prompt=SCORING_SYSTEM_PROMPT, preferred_model=model_a)[0],
            {str(item["id"]) for item in batch},
        )
        for item in batch:
            value = parsed[str(item["id"])]
            suggestions.append({
                "id": str(item["id"]),
                "model": model_a,
                "score": value["score"],
                "rationale": value["rationale"],
                "flags": value["flags"],
            })

    double_ids = {str(item["id"]) for item in selected if item.get("double_annotation_required")}
    if model_b and double_ids:
        double_items = [item for item in selected if str(item["id"]) in double_ids]
        for start in range(0, len(double_items), batch_size):
            batch = double_items[start:start + batch_size]
            parsed = parse_response(
                router.invoke_with_metadata(build_prompt(batch), system_prompt=SCORING_SYSTEM_PROMPT, preferred_model=model_b)[0],
                {str(item["id"]) for item in batch},
            )
            for item in batch:
                value = parsed[str(item["id"])]
                suggestions.append({
                    "id": str(item["id"]),
                    "model": model_b,
                    "score": value["score"],
                    "rationale": value["rationale"],
                    "flags": value["flags"],
                })

    return {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "model_a": model_a,
        "model_b": model_b,
        "items_requested": len(selected),
        "double_items_requested": len(double_ids),
        "suggestions": suggestions,
        "gold_status": "unannotated",
    }

def main() -> None:
    parser = argparse.ArgumentParser(description="Generate non-gold LLM assistance for J.A.R.V.I.S. annotation.")
    parser.add_argument("--input", default="eval/annotation_queue.json")
    parser.add_argument("--output", default="eval/annotation_assistance_v1.json")
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--model-a", default=LLM_DEFAULT_MODEL)
    parser.add_argument("--model-b", default=(LLM_FALLBACK_MODELS[0] if LLM_FALLBACK_MODELS else None))
    args = parser.parse_args()

    if args.batch_size <= 0:
        raise ValueError("batch-size must be positive")
    with open(args.input, "r", encoding="utf-8") as handle:
        records = json.load(handle)
    result = annotate_queue(records, args.batch_size, args.model_a, args.model_b, args.limit)
    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, ensure_ascii=False)
    print(f"Generated {len(result['suggestions'])} non-gold LLM suggestions in {args.output}")

if __name__ == "__main__":
    main()