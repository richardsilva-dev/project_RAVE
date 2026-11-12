$ErrorActionPreference = "Stop"

$LabRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
if (-not (Test-Path (Join-Path $LabRoot ".git"))) {
    throw "This is still a staging folder inside project_RAVE. Move the contents of benchmark_lab into the standalone rave-benchmark-lab repository before running this script."
}

$SubmoduleRelativePath = "comparison_b/upstream/open_deep_research"
$SubmodulePath = Join-Path $LabRoot $SubmoduleRelativePath
$UpstreamUrl = "https://github.com/langchain-ai/open_deep_research.git"
$PinnedSha = "1b7d2e80db9faa586165c60e09096dbbfd483a64"

if (-not (Test-Path $SubmodulePath)) {
    git -C $LabRoot submodule add $UpstreamUrl $SubmoduleRelativePath
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
