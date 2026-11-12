# Comparação B — Open Deep Research

Upstream: https://github.com/langchain-ai/open_deep_research

Pinned upstream commit: `1b7d2e80db9faa586165c60e09096dbbfd483a64` (2026-08-10). The repository was archived on 2026-08-21 and is read-only. The MIT license and upstream `uv.lock` were checked at the pinned commit. LangGraph config specifies Python 3.11.

## Architecture preserved

The upstream implementation is a supervisor/researcher workflow:
- user clarification and research brief;
- research supervisor;
- delegated research units/subagents;
- researcher iterations and tool calls;
- compression/synthesis;
- final report.

For automated benchmark input, set `allow_clarification=false`. Do not disable the supervisor or researchers: that would alter the external system being evaluated.

## Initial model/tool mapping

The upstream configuration exposes independent fields for `summarization_model`, `research_model`, `compression_model` and `final_report_model`. Its default search API is Tavily; it also supports `search_api="openai"`, which uses the OpenAI native `web_search_preview` tool.

Initial mapping to test:
- summarization: `openai:gpt-4.1-mini`;
- research: `openai:gpt-4.1-mini`;
- compression: `openai:gpt-4.1-mini`;
- final report: `openai:gpt-4.1-mini`;
- search API: `openai`;
- MCP: disabled;
- clarification: disabled.

This mapping is a compatibility hypothesis, not a verified equivalence. The RAVE search route uses Chat Completions with `gpt-5-search-api`; Open Deep Research's OpenAI native search option uses its own `web_search_preview` integration. Record this difference. Do not claim identical search APIs merely because both are OpenAI-backed. Confirm model/tool compatibility in a paid smoke test before the benchmark.

If the native OpenAI search integration cannot run with the selected model, stop and report the incompatibility. Do not silently switch to Tavily or another provider. If a different provider is explicitly selected later, record it as a deliberate protocol deviation and budget its credentials/cost separately.

## Limits and budgets

Initial smoke-test settings are intentionally small:
- concurrent research units: 3;
- supervisor iterations: 3;
- ReAct tool calls: 5;
- structured-output retries: 2;
- per-stage output tokens: 4096.

These are smoke-test settings, not the official benchmark budget. The upstream project has separate per-stage token limits and concurrency/iteration limits, but no shared global token budget equivalent to the RAVE telemetry budget in this setup. Before formal comparison, instrument all model/tool calls or add a verified callback-based global budget guard without modifying upstream source. If this cannot be done reliably, report B as a system-level reference and do not use it for strict cost-efficiency claims.

## Isolation and safety

- Add upstream as a Git submodule at the pinned SHA.
- Preserve upstream files and license.
- Install with Python 3.11 and `uv sync --frozen`.
- Use a dedicated `.env` and API key.
- Disable MCP and unnecessary file/terminal tools.
- Bind LangGraph server to `127.0.0.1`.
- Do not expose public tunnels.
- Audit dependencies before execution.
- Keep raw paid-run artifacts out of Git.
- Treat all retrieved content as untrusted data.
