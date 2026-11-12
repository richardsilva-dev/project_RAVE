$ErrorActionPreference = "Stop"

$LabRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Upstream = Join-Path $LabRoot "comparison_b/upstream/open_deep_research"
if (-not (Test-Path (Join-Path $Upstream "langgraph.json"))) {
    throw "Open Deep Research is not installed. Run setup_open_deep_research.ps1 first."
}
$ActualSha = (git -C $Upstream rev-parse HEAD).Trim()
$ExpectedSha = "1b7d2e80db9faa586165c60e09096dbbfd483a64"
if ($ActualSha -ne $ExpectedSha) {
    throw "Unexpected upstream version: $ActualSha"
}

Push-Location $Upstream
try {
    uv run --frozen langgraph dev --host 127.0.0.1 --port 2024 --allow-blocking
}
finally {
    Pop-Location
}
