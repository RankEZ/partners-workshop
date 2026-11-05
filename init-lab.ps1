# ===========================================================================
# Partner lab initializer (Windows PowerShell).
#
#   .\init-lab.ps1 7        -> non-interactive (partner 7)
#   .\init-lab.ps1          -> prompts for the partner ID
#
# Partner 1 -> subnet 10.101.0.0/24, partner 2 -> 10.102.0.0/24, etc.
#
# If PowerShell blocks execution (default policy), run:
#   powershell -ExecutionPolicy Bypass -File .\init-lab.ps1
#   powershell -ExecutionPolicy Bypass -File .\init-lab.ps1 7
# ===========================================================================

param(
    [Parameter(Position = 0)]
    [int]$PartnerId = 0
)

$ErrorActionPreference = "Stop"

# ---------------------------------------------------------------------------
# Partner ID: from the parameter, or prompted
# ---------------------------------------------------------------------------
if ($PartnerId -eq 0) {
    $answer = Read-Host "Enter partner ID (1, 2, 3, ...)"
    if ($answer -notmatch '^\d+$') {
        Write-Error "ERROR: partner ID must be a positive integer (e.g. 1, 2, 3)."
        exit 1
    }
    $PartnerId = [int]$answer
}

if ($PartnerId -lt 1) {
    Write-Error "ERROR: partner ID must be >= 1."
    exit 1
}

# ---------------------------------------------------------------------------
# Subnet / ports (identical math to init-lab.sh)
# ---------------------------------------------------------------------------
$octet = 100 + $PartnerId
if ($octet -gt 255) {
    Write-Error "ERROR: partner ID $PartnerId -> subnet 10.${octet}.0.0/24 is out of range (max ID 155)."
    exit 1
}
$subnet = "10.$octet.0"

$sshHostPort     = 22000 + $PartnerId   # proxy-client SSH
$webHostPort     = 8080                 # target-web HTTP (80 inside)
$sshWebHostPort  = 25000 + $PartnerId   # target-web SSH (CPM-for-File)

# ---------------------------------------------------------------------------
# Preflight: fail clearly before the partner has to debug Docker internals
# ---------------------------------------------------------------------------
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Error "ERROR: 'docker' not found. Install Docker Desktop first."
    exit 1
}
docker compose version 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Error "ERROR: 'docker compose' (v2 plugin) not found. Install Docker Compose v2."
    exit 1
}

# ---------------------------------------------------------------------------
# Write .env (docker-compose autoloads it).  LF line endings so it stays
# byte-identical in behaviour to the Linux script.
# ---------------------------------------------------------------------------
$envLines = @(
    "PARTNER_ID=$PartnerId",
    "LAB_SUBNET=$subnet",
    "SSH_HOST_PORT=$sshHostPort",
    "WEB_HOST_PORT=$webHostPort",
    "SSH_WEB_HOST_PORT=$sshWebHostPort"
)
[System.IO.File]::WriteAllText(
    (Join-Path $PSScriptRoot ".env"),
    (($envLines -join "`n") + "`n")
)

# ---------------------------------------------------------------------------
# Cheat sheet file (partners forget these)
# ---------------------------------------------------------------------------
$infoFile = "partner-$PartnerId.txt"
$infoLines = @(
    "==========================================================",
    " RankEZ Partner Lab #$PartnerId   subnet ${subnet}.0/24",
    "==========================================================",
    "",
    "Targets (inside the lab network):",
    "  Linux (SSH)       ${subnet}.10   port 22   (SSH)",
    "  Database (MySQL)  ${subnet}.20   port 3306",
    "  Web Portal        ${subnet}.30   port 80   (HTTP)",
    "",
    "Local test access (from the host):",
    "  SSH        ssh super@127.0.0.1 -p $sshHostPort",
    "  Web        http://127.0.0.1:$webHostPort",
    "  Web SSH    ssh super@127.0.0.1 -p $sshWebHostPort",
    "",
    "Credentials:",
    "  Linux users : super / oper / root",
    "  Linux pass  : RankEZ123!",
    "  MySQL root  : DBRootPassword123!",
    "  MySQL app   : app_user / AppPassword123!   (db: customer_db; app->DB service account)",
    "  Web logins  : demo / RankEZ123!  and  admin / Admin@Demo1  (portal users table)",
    "=========================================================="
)
[System.IO.File]::WriteAllText(
    (Join-Path $PSScriptRoot $infoFile),
    (($infoLines -join "`n") + "`n")
)

# ---------------------------------------------------------------------------
# Display the target map: IP + service port per tier
# ---------------------------------------------------------------------------
Write-Host "=========================================================="
Write-Host " Partner Lab #$PartnerId  ->  subnet ${subnet}.0/24"
Write-Host "=========================================================="
Write-Host ""
Write-Host ("{0,-16} {1,-18} {2,-8}" -f "Target Type", "Target IP", "Service Port")
Write-Host ("{0,-16} {1,-18} {2,-8}" -f "----------------", "------------------", "------------")
Write-Host ("{0,-16} {1,-18} {2,-8}" -f "Linux (SSH)", "${subnet}.10", "22 (SSH)")
Write-Host ("{0,-16} {1,-18} {2,-8}" -f "Database (MySQL)", "${subnet}.20", "3306")
Write-Host ("{0,-16} {1,-18} {2,-8}" -f "Web Portal", "${subnet}.30", "80 (HTTP)")
Write-Host ""
Write-Host "Local test ports (host): SSH $sshHostPort | Web $webHostPort | Web-SSH $sshWebHostPort"
Write-Host ""
Write-Host "Accounts: super / oper / root  (password: RankEZ123!)"
Write-Host "MySQL:    app_user / AppPassword123!  (db: customer_db; app->DB service account)"
Write-Host "Web:      demo / RankEZ123!  and  admin / Admin@Demo1  (portal login, users table)"
Write-Host "=========================================================="
Write-Host "Saved cheat sheet (targets + passwords): $infoFile  (git-ignored)"
Write-Host "Next step: Run 'docker compose up -d --build'"