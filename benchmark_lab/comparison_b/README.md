# Comparison B — Open Deep Research

Upstream repository: https://github.com/langchain-ai/open_deep_research

This folder is a preparation placeholder. The upstream project must be added as a Git submodule only after this staging directory has been moved into the independent `rave-benchmark-lab` repository.

## Required setup

1. Run `git submodule add https://github.com/langchain-ai/open_deep_research.git comparison_b/upstream/open_deep_research`.
2. Record the full checked-out SHA in `comparison_b/UPSTREAM_VERSION.md`.
3. Verify license and archived status from upstream metadata at setup time.
4. Read upstream README, pyproject and lockfile before installation.
5. Create an independent Python 3.11 environment.
6. Preserve the upstream lockfile and avoid upgrades.
7. Disable unnecessary MCP, filesystem and terminal tools.
8. Bind local server to 127.0.0.1 only.
9. Run a non-benchmark smoke test.

Do not claim that Comparison B is installed or executable until the submodule, pinned SHA, dependencies, model mapping and smoke test have been verified.
