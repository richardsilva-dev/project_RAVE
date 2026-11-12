from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

_TRACKING = {"fbclid", "gclid", "dclid", "msclkid", "igshid", "mc_cid", "mc_eid"}


def canonicalize_url(value: str) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parts = urlsplit(value.strip())
        scheme = parts.scheme.lower()
        if scheme not in {"http", "https"} or not parts.hostname:
            return None
        if parts.username is not None or parts.password is not None:
            return None
        host = parts.hostname.encode("idna").decode("ascii").lower()
        port = parts.port
        if ":" in host and not host.startswith("["):
            host = f"[{host}]"
        netloc = host
        if port and not ((scheme == "http" and port == 80) or (scheme == "https" and port == 443)):
            netloc += f":{port}"
        path = parts.path or "/"
        if path != "/":
            path = path.rstrip("/") or "/"
        query = sorted((k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)
                       if not k.lower().startswith("utm_") and k.lower() not in _TRACKING)
        return urlunsplit((scheme, netloc, path, urlencode(query), ""))
    except (UnicodeError, ValueError, TypeError):
        return None
