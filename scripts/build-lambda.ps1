[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$backendDir = Join-Path $repoRoot 'backend'
$distDir = Join-Path $backendDir 'lambda_dist'
$requirementsPath = Join-Path $distDir 'requirements.txt'
$zipPath = Join-Path $repoRoot 'infra\backend.zip'
$sourcePath = Join-Path $backendDir 'src\opendoor_relay'
$lockPath = Join-Path $backendDir 'uv.lock'

Push-Location $backendDir
try {
    if (Test-Path $distDir) {
        Remove-Item -Recurse -Force $distDir
    }
    New-Item -ItemType Directory -Force -Path $distDir | Out-Null

    if (Test-Path $lockPath) {
        & uv export --frozen --no-dev --no-emit-project --format requirements-txt --output-file $requirementsPath
    }
    else {
        Write-Warning 'backend/uv.lock is missing; resolving dependencies before export.'
        & uv export --no-dev --no-emit-project --format requirements-txt --output-file $requirementsPath
    }
    if ($LASTEXITCODE -ne 0) { throw 'uv export failed' }

    # Build Linux-compatible Python 3.12 wheels even when this script runs on Windows.
    & uv pip install -r $requirementsPath --target $distDir --python-version 3.12 --python-platform linux --only-binary ':all:'
    if ($LASTEXITCODE -ne 0) { throw 'Lambda dependency installation failed' }

    Copy-Item -Path $sourcePath -Destination (Join-Path $distDir 'opendoor_relay') -Recurse

    $uncompressedBytes = (Get-ChildItem $distDir -Recurse -File | Measure-Object -Property Length -Sum).Sum
    if ($uncompressedBytes -gt 250MB) {
        throw "Lambda package exceeds the 250 MB uncompressed limit: $uncompressedBytes bytes"
    }

    if (Test-Path $zipPath) {
        Remove-Item -Force $zipPath
    }
    Compress-Archive -Path (Join-Path $distDir '*') -DestinationPath $zipPath -Force

    $zip = Get-Item $zipPath
    Write-Host ("Lambda bundle created: {0:N1} MB compressed, {1:N1} MB uncompressed" -f ($zip.Length / 1MB), ($uncompressedBytes / 1MB))
}
finally {
    Pop-Location
}
