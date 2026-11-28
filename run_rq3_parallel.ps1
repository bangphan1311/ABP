$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$outDir = "results/rq3_official"
$archiveDir = "$outDir/attempt_history"
$maxParallel = 3

if (Test-Path $outDir) {
    New-Item -ItemType Directory -Force $archiveDir | Out-Null
    Get-ChildItem "$outDir/*.json" -ErrorAction SilentlyContinue | Where-Object {
        (Get-Content $_.FullName -Raw | ConvertFrom-Json).status -eq "MO"
    } | ForEach-Object {
        Write-Host "Archiving MO for retry: $($_.Name)"
        Move-Item $_.FullName $archiveDir -Force
    }
}

function Get-RunnerArgs($row) {
    $a = @(
        "-m", "src.runner",
        "--instance", "benchmark/hb/raw/$($row.filename)",
        "--method", $row.method,
        "--seed", "0",
        "--time-limit", $row.time_limit_s,
        "--memory-limit", $row.memory_limit_gib,
        "--out", $outDir,
        "--resume"
    )
    if ($row.method -eq "sat") {
        $a += @("--abp-encoding", $row.abp_encoding, "--amo-encoding", $row.amo_encoding, "--sat-solver", $row.solver)
    }
    return $a
}

$running = @()
Import-Csv "results/official-plan.csv" | ForEach-Object {
    $running = @($running | Where-Object { -not $_.Proc.HasExited })
    while ($running.Count -ge $maxParallel) {
        Start-Sleep -Seconds 2
        $running = @($running | Where-Object { -not $_.Proc.HasExited })
    }
    $proc = Start-Process -FilePath ".venv\Scripts\python.exe" -ArgumentList (Get-RunnerArgs $_) -PassThru -NoNewWindow
    $running += [pscustomobject]@{ Proc = $proc; Instance = $_.instance_id; Method = $_.method }
    Write-Host "started $($_.instance_id) $($_.method) pid=$($proc.Id)"
}

$running | ForEach-Object { $_.Proc.WaitForExit() }
Write-Host "all tasks finished"
