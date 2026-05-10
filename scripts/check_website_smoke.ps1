$ErrorActionPreference = "Stop"

$root = Resolve-Path "$PSScriptRoot\.."
$backendOut = Join-Path $env:TEMP "task6-backend-smoke.out.log"
$backendErr = Join-Path $env:TEMP "task6-backend-smoke.err.log"
$frontendOut = Join-Path $env:TEMP "task6-frontend-smoke.out.log"
$frontendErr = Join-Path $env:TEMP "task6-frontend-smoke.err.log"
$backendPort = 5055
$frontendPort = 5174

function Wait-HttpOk {
    param(
        [string]$Url,
        [int]$TimeoutSeconds = 60
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    do {
        try {
            $response = Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec 3
            if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 500) {
                return $response
            }
        }
        catch {
            Start-Sleep -Milliseconds 500
        }
    } while ((Get-Date) -lt $deadline)

    throw "Timed out waiting for $Url"
}

function Wait-BackendLogin {
    param([int]$TimeoutSeconds = 60)

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    $body = '{"username":"admin","password":"123456"}'
    do {
        try {
            $response = Invoke-RestMethod `
                -Method Post `
                -Uri "http://127.0.0.1:$backendPort/api/auth/login" `
                -ContentType "application/json" `
                -Body $body `
                -TimeoutSec 3
            if ($response.code -eq 200) {
                return
            }
        }
        catch {
            Start-Sleep -Milliseconds 500
        }
    } while ((Get-Date) -lt $deadline)

    throw "Timed out waiting for backend login endpoint."
}

$backend = $null
$frontend = $null

try {
    $occupiedPorts = Get-NetTCPConnection -LocalPort $backendPort,$frontendPort -State Listen -ErrorAction SilentlyContinue
    if ($occupiedPorts) {
        $ports = ($occupiedPorts | Select-Object -ExpandProperty LocalPort -Unique) -join ", "
        throw "Port(s) already in use before smoke test: $ports. Stop existing dev servers first."
    }

    $backend = Start-Process `
        -FilePath (Join-Path $root "venv\Scripts\python.exe") `
        -ArgumentList "`"$(Join-Path $root "scripts\run_backend_smoke_server.py")`"" `
        -WorkingDirectory $root `
        -RedirectStandardOutput $backendOut `
        -RedirectStandardError $backendErr `
        -WindowStyle Hidden `
        -PassThru

    Wait-BackendLogin

    $oldProxyTarget = $env:VITE_API_PROXY_TARGET
    $env:VITE_API_PROXY_TARGET = "http://127.0.0.1:$backendPort"

    $frontend = Start-Process `
        -FilePath "node" `
        -ArgumentList "node_modules\vite\bin\vite.js", "--host", "127.0.0.1", "--port", "$frontendPort" `
        -WorkingDirectory (Join-Path $root "frontend") `
        -RedirectStandardOutput $frontendOut `
        -RedirectStandardError $frontendErr `
        -WindowStyle Hidden `
        -PassThru

    $loginPage = Wait-HttpOk "http://127.0.0.1:$frontendPort/login.html"
    if ($loginPage.Content -notmatch "loginForm") {
        throw "Login page did not contain the expected login form marker."
    }

    $homePage = Wait-HttpOk "http://127.0.0.1:$frontendPort/"
    if ($homePage.Content -notmatch "<div id=`"app`"></div>") {
        throw "Home page did not contain the Vue app mount point."
    }

    $loginBody = '{"username":"admin","password":"123456"}'
    $login = Invoke-RestMethod `
        -Method Post `
        -Uri "http://127.0.0.1:$frontendPort/api/auth/login" `
        -ContentType "application/json" `
        -Body $loginBody `
        -TimeoutSec 10

    if ($login.code -ne 200 -or -not $login.data.access_token) {
        throw "Login through Vite proxy failed."
    }

    $headers = @{ Authorization = "Bearer $($login.data.access_token)" }
    $trend = Invoke-RestMethod `
        -Method Get `
        -Uri "http://127.0.0.1:$frontendPort/api/emotion/trend" `
        -Headers $headers `
        -TimeoutSec 10

    if ($trend.code -ne 200 -or $null -eq $trend.data) {
        throw "Emotion trend through Vite proxy failed."
    }

    Write-Host "Website smoke test passed."
}
finally {
    if (Get-Variable -Name oldProxyTarget -Scope Local -ErrorAction SilentlyContinue) {
        $env:VITE_API_PROXY_TARGET = $oldProxyTarget
    }
    if ($frontend -and -not $frontend.HasExited) {
        Stop-Process -Id $frontend.Id -Force
    }
    if ($backend -and -not $backend.HasExited) {
        Stop-Process -Id $backend.Id -Force
    }
}
