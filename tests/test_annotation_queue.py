from src.evaluation.prepare_annotation_queue import prepare_queue


def make_item(item_id: int, split: str, area: str) -> dict:
    return {
        "id": str(item_id),
        "title": f"Article {item_id}",
        "summary": "Summary",
        "area": area,
        "source": "TestSource",
        "domain": "example.com",
        "published": "2026-09-21T00:00:00+00:00",
        "url": f"https://example.com/{item_id}",
        "canonical_url": f"https://example.com/{item_id}",
        "duplicate_group": None,
        "split": split,
    }


def test_prepare_queue_is_reproducible_and_preserves_size():
    corpus = [
        make_item(i, "test" if i % 2 else "dev", ["TECH", "FINANCE"][i % 2])
        for i in range(20)
    ]
    queue_a, double_a, manifest_a = prepare_queue(corpus, 0.20, 42)
    queue_b, double_b, manifest_b = prepare_queue(corpus, 0.20, 42)
    assert queue_a == queue_b
    assert double_a == double_b
    assert manifest_a == manifest_b
    assert len(queue_a) == 20
    assert len(double_a) == 4


def test_prepare_queue_marks_double_annotation_records():
    corpus = [make_item(i, "test", "TECH" if i < 5 else "WORLD") for i in range(20)]
    queue, double_queue, manifest = prepare_queue(corpus, 0.20, 42)
    assert all(item["double_annotation_required"] for item in double_queue)
    assert all(
        not item["double_annotation_required"]
        for item in queue
        if item not in double_queue
    )
    assert manifest["gold_status"] == "unannotated"
