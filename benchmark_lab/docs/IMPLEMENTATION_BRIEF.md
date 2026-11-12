# Codex implementation brief — RAVE Benchmark Lab

## Current staging constraint

This folder is staged in the private `project_RAVE` repository on branch `benchmark-preparation` because the available GitHub integration cannot create a new repository. Before formal use, create a separate private repository `rave-benchmark-lab` and move this folder's contents to its root. Do not merge this staging folder into the RAVE `main` branch.

## Work already scaffolded

- Standalone SOLO package and CLI.
- Sequential single-agent research loop.
- Separate settings and environment variables.
- Search/model call budget and telemetry.
- JSON request schema.
- URL canonicalization for the SOLO result pipeline.
- Comparison A/B and security protocol documents.
- Basic tests for budget and URL normalization.

## Codex must complete and verify

1. Inspect the current RAVE branch and confirm actual model IDs, endpoint, search payload, request limits, output contracts and token accounting.
2. Compare the SOLO client payload with `rave/llm.py`; align only documented parameters. Do not import RAVE modules into the SOLO package.
3. Add a shared result schema and metadata schema, including run IDs, commit SHAs, model IDs, provider, prompt/scope, calls, retries, tokens, duration, status, failure reason, sources and citations.
4. Validate every model JSON response; invalid/incomplete output must not receive COMPLETED status.
5. Ensure the solo loop is sequential and cannot instantiate or delegate to other agents.
6. Ensure all budget limits are checked before each request where possible and after provider token usage is returned. Document token overshoot limits.
7. Add tests for provider errors, malformed JSON, invalid citations, budget exhaustion, timeouts and status classification.
8. Add CI for Python 3.11 and run the tests without API credentials.
9. Obtain the official Open Deep Research submodule commit SHA and pin it. Record its archive/read-only status and MIT license only after verifying current upstream metadata.
10. Audit upstream dependencies and check the actual current install instructions before creating its isolated environment.
11. Implement a small runner/adapter for Open Deep Research without rewriting upstream source. Capture model/tool configuration and output metadata.
12. Add an adapter for the exact RAVE run JSON schema and normalize all three outputs without deleting source provenance or system-specific metadata.
13. Add a preflight command that checks configuration presence, model/tool compatibility, budget values, loopback binding and secrets exposure without making paid calls.
14. Add smoke-test instructions. Use a separate non-benchmark question.
15. Do not create the official question set, blind scoring, evaluator, statistical analysis or final superiority claims in this phase.

## Acceptance criteria

- `pytest -q` passes on Python 3.11 without API credentials.
- Solo output is valid JSON with a truthful COMPLETED/PARTIAL/INVALID status.
- One and only one researcher exists; there is no delegation or inter-agent communication.
- Search provider, model IDs, parameters, calls, tokens, runtime and failure status are recorded.
- Open Deep Research is pinned to a full commit SHA, isolated and not rewritten.
- All differences between RAVE, SOLO and Open Deep Research are explicitly documented.
- No secrets are present in Git history or logs.
- No official benchmark execution begins before the protocol is preregistered.
