# Expose AI Factory React console via ngrok with HTTP basic auth.
# Prerequisites:
#   1. API on :8001 and React on :5173 (.\ai_factory_ui\scripts\start-console.ps1)
#   2. ngrok installed + authtoken: ngrok config add-authtoken <YOUR_TOKEN>
#      Get token: https://dashboard.ngrok.com/get-started/your-authtoken
#
# Usage:
#   .\scripts\start-ngrok.ps1
#   .\scripts\start-ngrok.ps1 -User demo -Password 'secret'
#   $env:NGROK_BASIC_USER='demo'; $env:NGROK_BASIC_PASS='secret'; .\scripts\start-ngrok.ps1

param(
    [string]$User = $(if ($env:NGROK_BASIC_USER) { $env:NGROK_BASIC_USER } else { "aifactory" }),
    [string]$Password = $(if ($env:NGROK_BASIC_PASS) { $env:NGROK_BASIC_PASS } else { "" }),
    [int]$Port = 5173
)

$ErrorActionPreference = "Stop"

$ngrok = Get-Command ngrok -ErrorAction SilentlyContinue
if (-not $ngrok) {
    $wingetNgrok = Get-ChildItem "$env:LOCALAPPDATA\Microsoft\WinGet\Packages" -Filter "ngrok.exe" -Recurse -ErrorAction SilentlyContinue |
        Select-Object -First 1 -ExpandProperty FullName
    $candidates = @(
        $wingetNgrok
        "$env:LOCALAPPDATA\ngrok\ngrok.exe"
        "$env:ProgramFiles\ngrok\ngrok.exe"
        "$PSScriptRoot\..\..\tools\ngrok.exe"
    ) | Where-Object { $_ }
    foreach ($c in $candidates) {
        if (Test-Path $c) {
            $ngrok = @{ Source = $c }
            break
        }
    }
}
if (-not $ngrok) {
    Write-Error "ngrok not found. Install: winget install ngrok.ngrok   then: ngrok config add-authtoken <token>"
}

if (-not $Password) {
    $secure = Read-Host "Basic-auth password for remote access" -AsSecureString
    $Password = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
        [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    )
    if (-not $Password) {
        Write-Error "Password is required for ngrok basic auth."
    }
}

try {
    $listening = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
} catch {
    $listening = $null
}
if (-not $listening) {
    Write-Warning "Nothing is listening on port $Port. Start the React console first (npm run dev in AI-Factory-React)."
}

Write-Host "Starting ngrok → http://127.0.0.1:$Port"
Write-Host "Basic auth user: $User"
Write-Host "Share only the HTTPS URL from the ngrok UI / terminal. Keep the password private."
Write-Host ""

& $ngrok.Source http $Port --basic-auth="${User}:${Password}"
