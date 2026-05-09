$ErrorActionPreference = "Stop"

Push-Location "$PSScriptRoot\..\frontend"
try {
    npm run build

    $distIndex = Join-Path (Get-Location) "dist\index.html"
    if (-not (Test-Path $distIndex)) {
        throw "Vite build completed but dist\index.html was not generated."
    }

    Write-Host "Frontend build smoke test passed."
}
finally {
    Pop-Location
}
