$ErrorActionPreference = "Stop"

$UpstreamPath = Join-Path $PSScriptRoot "..\comparison_b\upstream\open_deep_research"
if (-not (Test-Path (Join-Path $PSScriptRoot "..\.gitmodules"))) {
    throw "This is a staging copy. Move benchmark_lab contents to the standalone rave-benchmark-lab repository first, then add the upstream project as a Git submodule."
}
if (-not (Test-Path $UpstreamPath)) {
    throw "Open Deep Research submodule is missing. Add it from the official LangChain repository and pin a full commit SHA before setup."
}

Push-Location $UpstreamPath
try {
    if (-not (Test-Path "pyproject.toml")) {
        throw "Upstream pyproject.toml was not found; inspect the checked-out revision before proceeding."
    }
    if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
        throw "uv is required. Install it before continuing."
    }
    uv venv
    uv sync --frozen
}
finally {
    Pop-Location
}
