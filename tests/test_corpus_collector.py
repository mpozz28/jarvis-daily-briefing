from src.evaluation.collect_real_corpus import classify_area, normalize_text, normalize_url, parse_published


def test_normalize_url_removes_tracking_parameters():
    url = "https://Example.com/story/?utm_source=test&foo=bar#section"
    assert normalize_url(url) == "https://example.com/story?foo=bar"


def test_normalize_text_strips_html_and_collapses_whitespace():
    assert normalize_text("<p>Hello&nbsp;world</p>\n next") == "Hello world next"


def test_parse_published_handles_rfc822():
    value = parse_published({"published": "Mon, 21 Sep 2026 10:00:00 GMT"})
    assert value == "2026-09-21T10:00:00+00:00"


def test_classify_area_prefers_explicit_ai_feed():
    assert classify_area("A paper on economics", "A research result about neural networks", "AI/ML") == "AI/ML"


def test_classify_area_detects_finance():
    assert classify_area("Markets react to new inflation data", "Stocks move after the latest report.", "OTHER") == "FINANCE"
