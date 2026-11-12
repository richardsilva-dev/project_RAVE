# Result adapters

The adapters must normalize RAVE, SOLO and Open Deep Research outputs into the schemas in `contracts/` while preserving system-specific fields.

Rules:
- Never fabricate fields missing from source output.
- Keep provider-returned citations separate from model-reported references.
- Keep canonical URL and original URL values.
- Preserve status and failure reason.
- Do not map a partial or invalid run to COMPLETED.
- Preserve model IDs, provider, tool configuration, token counts, retries, timing and version SHAs.
- Keep the original raw JSON in a private, ignored artifact directory; do not commit paid-run raw outputs by default.
