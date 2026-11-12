# Codex implementation brief — RAVE Benchmark Lab

## Current staging constraint

This folder is staged in the private `project_RAVE` repository on branch `benchmark-preparation` because the available GitHub integration did not expose a create-repository operation. Create a separate private repository `rave-benchmark-lab` and move the contents of this folder to its root before formal experiments. Do not merge this staging folder into the RAVE `main` branch.

## Implemented in the staging branch

- Standalone SOLO Python package with its own settings and API key namespace.
- One sequential researcher with planning, gap-directed follow-up searches, analysis and final synthesis; no delegation or inter-agent messaging.
- Model/search call budget, runtime/token accounting, per-call telemetry and bounded 429 retry behavior.
- Provider-returned citation collection, URL canonicalization, final citation checks against provider-returned URLs and rejection of invented final references.
- JSON request/result/metadata schemas.
- RAVE, SOLO and explicit Open Deep Research result adapters that preserve native metadata and do not promote partial runs.
- Comparison A and B protocols, architecture, security policy and implementation brief.
- Open Deep Research upstream commit pinned in documentation: `1b7d2e80db9faa586165c60e09096dbbfd483a64`; upstream README, pyproject, LangGraph configuration, lockfile presence and MIT license inspected at that commit.
- Initial Open Deep Research model/search mapping, isolated setup/run scripts and preflight check.
- CI workflow for the standalone SOLO package.
- RAVE synthesis schema validation and canonical URL deduplication fixes with regression tests.

## CI evidence

On the latest PR head at the time of verification:
- RAVE `tests` workflow: 32 passed, run #18, success.
- `benchmark-lab-tests` workflow: 10 passed, run #30, success.

These are automated tests only. No paid API smoke test or Open Deep Research runtime test was executed.

## Codex must complete before formal experiments

1. Create/move this staging folder into a standalone private repository `rave-benchmark-lab`; keep RAVE as a separate repository.
2. Add the official Open Deep Research repository as a Git submodule at `comparison_b/upstream/open_deep_research`, then checkout the exact pinned SHA above and commit the gitlink plus `.gitmodules`.
3. Run the PowerShell setup script from the standalone lab root; verify Python 3.11, `uv sync --frozen`, dependency audit and upstream license.
4. Verify the exact RAVE model IDs, request payload, endpoint, temperature, search context, retry policy, token accounting and call limits from the current RAVE commit. Align SOLO only where technically compatible and document any remaining difference.
5. Add SOLO tests for provider errors, invalid planner/analyst/final JSON, invalid citations, token overshoot, timeout, budget exhaustion and partial/invalid status. Ensure failed calls are recorded.
6. Verify SOLO and RAVE use the same model IDs and hosted search provider for Comparison A. A shared provider label alone is not proof of identical endpoints or behavior.
7. Configure Open Deep Research with clarification disabled, MCP disabled and OpenAI native web search only if the selected model supports it. Perform a small paid smoke test and stop on incompatibility; do not silently switch to Tavily.
8. Verify the Open Deep Research local server binds only to `127.0.0.1`.
9. Instrument or otherwise reliably capture all Open Deep Research model/tool calls and enforce a global budget before making efficiency claims. If global accounting cannot be made reliable without modifying upstream source, keep B as a system-level quality reference and exclude strict cost-efficiency conclusions.
10. Add an adapter integration test using a real exported RAVE run JSON and an explicitly extracted Open Deep Research report. Do not infer the final answer from message order.
11. Record code SHAs, upstream SHA, models, providers, tool configuration, limits, calls, retries, tokens, duration, status and source provenance in each run manifest.
12. Keep raw paid-run artifacts and secrets out of Git.

## Acceptance criteria

- Both CI workflows pass on the standalone lab repository after migration.
- SOLO completes an independent smoke test and produces a valid result contract.
- Exactly one researcher is instantiated; there is no delegation or inter-agent communication.
- RAVE and SOLO model/search parity is verified or deviations are documented.
- Open Deep Research is installed at the pinned SHA, isolated and unmodified.
- All three adapters preserve source provenance, system-specific metadata and execution status.
- Global budget accounting is verified before cost/efficiency comparison.
- No secrets appear in Git history or logs.
- No official benchmark questions are executed before the experimental protocol is preregistered.

## Explicitly out of scope

Do not create the official question set, blind evaluator, scoring rubric, statistical analysis, result ranking or superiority claim in this implementation phase.
