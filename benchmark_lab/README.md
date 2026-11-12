# RAVE Benchmark Lab — staging area

> **Staging notice:** the GitHub integration available for this task can create branches and files in an existing repository, but it does not expose a create-repository operation. To avoid falsely claiming that a separate repository exists, this directory is a bootstrap copy on the isolated `benchmark-preparation` branch. It must be exported to a new private repository named `rave-benchmark-lab` before formal experiments. It is not imported by the RAVE runtime.

## Purpose

Prepare two distinct comparisons:

- **A — controlled SOLO baseline:** one researcher process, one decision-maker, sequential research loop, same configured RAVE model identifiers and the same hosted web-search route where supported.
- **B — external reference:** upstream LangChain Open Deep Research, preserved as an external system and pinned to an exact commit before execution.

The RAVE branch and this staging directory must remain separate from the RAVE `main` branch. Do not merge the lab into RAVE's runtime package.

## Comparison A

This standalone package intentionally does not import `rave`. It has its own configuration, API client, sequential research loop, budget counters, JSON result, and tests.

Run from this directory:

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
python -m solo_baseline.cli --question "YOUR QUESTION" --scope "YOUR SCOPE"
pytest -q
```

The API key is read from `SOLO_API_KEY`; do not copy the RAVE `.env`. The initial configuration defaults to the RAVE reference model IDs `gpt-4.1-mini` and `gpt-5-search-api`, but exact compatibility must be confirmed in a smoke test.

## Comparison B

Upstream: https://github.com/langchain-ai/open_deep_research

The upstream repository is archived/read-only as of 2026-08-21 according to the repository status checked during preparation. Before running it, the operator/Codex must:

1. Clone it as a Git submodule in the eventual standalone lab repository.
2. Record the full upstream commit SHA.
3. Preserve the upstream license and source tree.
4. Create an independent Python 3.11 environment and preserve the upstream lockfile.
5. Audit dependencies and tool permissions.
6. Map model and search configuration; record incompatibilities rather than silently substituting providers.
7. Run only on loopback and disable unnecessary MCP/filesystem/terminal integrations.

No upstream code has been rewritten or vendored into this staging directory.

## Experimental status

This is environment preparation, not a benchmark. There is no official question set, blind evaluator, scoring rubric, statistical analysis, or claim of superiority here. Do not compare answer quality until both systems have passed their smoke tests and a preregistered protocol defines common questions, context, budget, model IDs, search provider, and repetition policy.
