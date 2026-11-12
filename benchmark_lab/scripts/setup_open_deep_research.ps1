$ErrorActionPreference = "Stop"

$LabRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$RepoRoot = (Resolve-Path (Join-Path $LabRoot "..")).Path
$SubmoduleRelativePath = "benchmark_lab/comparison_b/upstream/open_deep_research"
$SubmodulePath = Join-Path $RepoRoot $SubmoduleRelativePath
$UpstreamUrl = "https://github.com/langchain-ai/open_deep_research.git"
$PinnedSha = "1b7d2e80db9faa586165c60e09096dbbfd483a64"

if (-not (Test-Path (Join-Path $RepoRoot ".git"))) {
    throw "Run this script from a Git checkout after moving the benchmark_lab folder into the standalone repository."
}

if (-not (Test-Path $SubmodulePath)) {
    git -C $RepoRoot submodule add $UpstreamUrl $SubmoduleRelativePath
    if ($LASTEXITCODE -ne 0) { throw "Could not add the official Open Deep Research submodule." }
}

git -C $SubmodulePath fetch origin $PinnedSha
if ($LASTEXITCODE -ne 0) { throw "Could not fetch the pinned upstream commit." }
git -C $SubmodulePath checkout --detach $PinnedSha
if ($LASTEXITCODE -ne 0) { throw "Could not check out the pinned upstream commit." }

$ActualSha = (git -C $SubmodulePath rev-parse HEAD).Trim()
if ($ActualSha -ne $PinnedSha) { throw "Upstream SHA mismatch. Expected $PinnedSha, got $ActualSha." }

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    throw "uv is required. Install uv before continuing."
}

Push-Location $SubmodulePath
try {
    if (-not (Test-Path "uv.lock") -or -not (Test-Path "pyproject.toml")) {
        throw "Pinned upstream lockfile or pyproject.toml is missing."
    }
    uv venv --python 3.11
    if ($LASTEXITCODE -ne 0) { throw "Could not create the isolated Python environment." }
    uv sync --frozen
    if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed; do not update the lockfile automatically." }
}
finally {
    Pop-Location
}
Write-Output "Open Deep Research pinned and installed at $ActualSha"
