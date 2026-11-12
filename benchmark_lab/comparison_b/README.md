# Comparison B — Open Deep Research

Upstream repository: https://github.com/langchain-ai/open_deep_research

Pinned version: `1b7d2e80db9faa586165c60e09096dbbfd483a64`.

The upstream project is archived/read-only. The pin, license, Python version and lockfile were verified from the upstream repository. The submodule must be added after this staging folder is moved to the standalone `rave-benchmark-lab` repository.

## Setup on Windows

From the standalone lab repository root:

```powershell
.\scripts\setup_open_deep_research.ps1
Copy-Item .\comparison_b\.env.example .\comparison_b\upstream\open_deep_research\.env
```

Set only the dedicated `OPENAI_API_KEY` in the upstream `.env`. Do not copy the RAVE or SOLO environment file.

Start the local server:

```powershell
.\comparison_b\run_local.ps1
```

The server is explicitly bound to `127.0.0.1:2024`. Do not expose a public tunnel.

In LangGraph Studio, create an assistant configuration using the fields in `config.example.json`. Disable clarification, MCP and any unneeded tools. The example uses OpenAI native web search; compatibility with the selected model must be verified by a smoke test. Do not silently fall back to Tavily.

Do not run benchmark questions until the formal protocol and global budget instrumentation are approved.
