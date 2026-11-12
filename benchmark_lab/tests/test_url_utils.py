from solo_baseline.url_utils import canonicalize_url


def test_tracking_parameters_and_fragments_are_removed():
    assert canonicalize_url("HTTPS://Example.org/a/?utm_source=x#part") == "https://example.org/a"


def test_meaningful_query_is_preserved():
    assert canonicalize_url("https://example.org/a?id=2") == "https://example.org/a?id=2"


def test_non_http_url_is_rejected():
    assert canonicalize_url("file:///tmp/private") is None
