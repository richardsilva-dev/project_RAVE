"""Canonical URL normalization for evidence deduplication.

Only known tracking parameters are removed. Query parameters that may change
resource identity are retained. The original URL should be preserved separately
when provenance requires it.
"""
from __future__ import annotations

import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

_TRACKING_KEYS = {
    "fbclid", "gclid", "dclid", "msclkid", "twclid", "ttclid",
    "igshid", "mc_cid", "mc_eid", "ref_src", "vero_id",
    "_hsenc", "_hsmi", "mkt_tok", "oly_anon_id", "oly_enc_id",
}
_PERCENT_ESCAPE = re.compile(r"%[0-9a-fA-F]{2}")


def canonicalize_url(value: str) -> str | None:
    """Return a stable HTTP(S) URL or None for malformed/unsafe URL values."""
    if not isinstance(value, str) or not value.strip():
        return None
    raw = value.strip()
    try:
        parts = urlsplit(raw)
        scheme = parts.scheme.lower()
        if scheme not in {"http", "https"} or not parts.hostname:
            return None
        if parts.username is not None or parts.password is not None:
            return None
        hostname = parts.hostname.encode("idna").decode("ascii").lower()
        try:
            port = parts.port
        except ValueError:
            return None
        if ":" in hostname and not hostname.startswith("["):
            hostname = f"[{hostname}]"
        netloc = hostname
        if port is not None and not ((scheme == "http" and port == 80) or
                                     (scheme == "https" and port == 443)):
            netloc = f"{netloc}:{port}"
        path = parts.path or "/"
        path = _PERCENT_ESCAPE.sub(lambda match: match.group(0).upper(), path)
        if path != "/":
            path = path.rstrip("/") or "/"
        query_items = []
        for key, item_value in parse_qsl(parts.query, keep_blank_values=True):
            lowered = key.lower()
            if lowered.startswith("utm_") or lowered in _TRACKING_KEYS:
                continue
            query_items.append((key, item_value))
        query_items.sort(key=lambda item: (item[0], item[1]))
        query = urlencode(query_items, doseq=True)
        return urlunsplit((scheme, netloc, path, query, ""))
    except (UnicodeError, ValueError, TypeError):
        return None
