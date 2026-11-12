import pytest

from rave.url_utils import canonicalize_url


@pytest.mark.parametrize("raw, expected", [
    ("HTTPS://Example.ORG:443/report/?utm_source=chatgpt.com#section",
     "https://example.org/report"),
    ("https://example.org/report?fbclid=abc&b=2&a=1",
     "https://example.org/report?a=1&b=2"),
    ("http://Example.org:80/a/",
     "http://example.org/a"),
    ("https://example.org/report?version=2",
     "https://example.org/report?version=2"),
])
def test_canonicalize_url_normalizes_only_safe_variants(raw, expected):
    assert canonicalize_url(raw) == expected


@pytest.mark.parametrize("raw", [
    "",
    "not a URL",
    "file:///etc/passwd",
    "ftp://example.org/file",
    "https://user:password@example.org/private",
    "https:///missing-host",
])
def test_canonicalize_url_rejects_invalid_or_unsafe_urls(raw):
    assert canonicalize_url(raw) is None


def test_canonicalize_url_preserves_meaningful_query_parameters():
    assert canonicalize_url("https://example.org/item?id=123&utm_campaign=spring") == (
        "https://example.org/item?id=123"
    )
