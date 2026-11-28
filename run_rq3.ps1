$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$outDir = "results/rq3_official"
$archiveDir = "$outDir/attempt_history"

if (Test-Path $outDir) {
    New-Item -ItemType Directory -Force $archiveDir | Out-Null
    Get-ChildItem "$outDir/*.json" -ErrorAction SilentlyContinue | Where-Object {
        (Get-Content $_.FullName -Raw | ConvertFrom-Json).status -eq "MO"
    } | ForEach-Object {
        Write-Host "Archiving MO for retry: $($_.Name)"
        Move-Item $_.FullName $archiveDir -Force
    }
}

Import-Csv "results/official-plan.csv" | ForEach-Object {
    $runnerArgs = @(
        "-m", "src.runner",
        "--instance", "benchmark/hb/raw/$($_.filename)",
        "--method", $_.method,
        "--seed", "0",
        "--time-limit", $_.time_limit_s,
        "--memory-limit", $_.memory_limit_gib,
        "--out", $outDir,
        "--resume"
    )
    if ($_.method -eq "sat") {
        $runnerArgs += @("--abp-encoding", $_.abp_encoding, "--amo-encoding", $_.amo_encoding, "--sat-solver", $_.solver)
    }
    .venv\Scripts\python.exe @runnerArgs
}
