[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

$releaseTag = 'v0.1.8'
$serverUrl = 'https://vibe.planlabopc.com'
$repository = 'https://github.com/JasonLuo365/vibe-course-marketplace.git'
$skillUrl = "https://raw.githubusercontent.com/JasonLuo365/vibe-course-marketplace/$releaseTag/plugins/claude-code/skills/submit-homework/SKILL.md"

function Ensure-Uv {
    if (Get-Command uv -ErrorAction SilentlyContinue) {
        return
    }

    Write-Host 'Installing uv...'
    Invoke-RestMethod https://astral.sh/uv/install.ps1 | Invoke-Expression
    $uvBin = Join-Path $HOME '.local\bin'
    if (Test-Path -LiteralPath $uvBin) {
        $env:Path = "$uvBin;$env:Path"
    }
    if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
        throw 'uv installation did not make the uv command available. Open a new terminal and run this installer again.'
    }
}

Ensure-Uv

$source = "git+$repository@$releaseTag#subdirectory=packages/vibe-submit"
Write-Host "Installing vibe-submit $releaseTag..."
& uv tool install --reinstall $source

$skillDir = Join-Path $HOME '.claude\skills\submit-homework'
New-Item -ItemType Directory -Path $skillDir -Force | Out-Null
Invoke-WebRequest -Uri $skillUrl -OutFile (Join-Path $skillDir 'SKILL.md')

[Environment]::SetEnvironmentVariable('VIBE_SUBMIT_SERVER_URL', $serverUrl, 'User')
$env:VIBE_SUBMIT_SERVER_URL = $serverUrl

Write-Host ''
Write-Host 'Installation complete.'
Write-Host 'Open a new terminal, run: vibe-submit setup'
Write-Host 'Then start Claude Code in your assignment directory and use: /submit-homework <assignment-code>'
