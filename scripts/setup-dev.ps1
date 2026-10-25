# Set up a darbit clone for development. Run once per clone, from anywhere:
#   pwsh scripts/setup-dev.ps1            # Python environment + skills link
#   pwsh scripts/setup-dev.ps1 -UI        # also npm install for the web UI
param([switch]$UI)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "uv is needed: winget install astral-sh.uv" -ForegroundColor Yellow
    exit 1
}

# Python 3.13, darbit (editable) and the dev tools, exactly as in uv.lock
uv sync

# lint before each commit
uv run pre-commit install

# Claude Code reads skills only from .claude/skills; the skills live in .agents/skills
# (docs/decisions/0004). A directory junction needs no admin rights and isn't committed.
$link = Join-Path $root ".claude\skills"
if (-not (Test-Path $link)) {
    New-Item -ItemType Directory -Force (Join-Path $root ".claude") | Out-Null
    New-Item -ItemType Junction -Path $link -Target (Join-Path $root ".agents\skills") | Out-Null
    Write-Host "linked .claude/skills -> .agents/skills"
}

if ($UI) {
    npm install
}

Write-Host "ready: uv run pytest, uv run ruff check ., uv run --group docs mkdocs serve"
