# Local skill installation only. Never deletes files or uploads task data.
[CmdletBinding()]
param(
    [ValidateSet('Install', 'Check')]
    [string]$Mode = 'Install',
    [string]$Destination,
    [switch]$Force
)
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$sourceDir = [System.IO.Path]::GetFullPath((Join-Path $repoRoot 'skills/focus'))
if (-not $Destination) {
    $skillBase = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $env:USERPROFILE '.codex' }
    $Destination = Join-Path $skillBase 'skills/focus'
}
$destinationDir = [System.IO.Path]::GetFullPath($Destination).TrimEnd([char]92, [char]47)
if ((Split-Path -Leaf $destinationDir) -ne 'focus') {
    throw 'Destination must be a dedicated folder named focus.'
}
if ($destinationDir -eq $sourceDir) {
    throw 'Source and installation destination must differ.'
}
$sourceFiles = @(Get-ChildItem -LiteralPath $sourceDir -Recurse -File |
    Where-Object { $_.FullName -notmatch '[\\/]__pycache__[\\/]' -and $_.Extension -ne '.pyc' })
$differences = @()
foreach ($file in $sourceFiles) {
    $relative = $file.FullName.Substring($sourceDir.Length).TrimStart([char]92, [char]47)
    $target = Join-Path $destinationDir $relative
    $matches = (Test-Path -LiteralPath $target -PathType Leaf) -and
        ((Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash -eq
         (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash)
    if (-not $matches) { $differences += $relative }
}
if ($Mode -eq 'Check') {
    if ($differences.Count) {
        Write-Output ('Source/installation differences: ' + ($differences -join ', '))
        exit 1
    }
    Write-Output ('Skill source and installation match: ' + $destinationDir)
    exit 0
}
if ((Test-Path -LiteralPath $destinationDir) -and $differences.Count -and -not $Force) {
    throw 'Installation differs. Review changes first; use -Force for an intentional source-to-install update.'
}
foreach ($file in $sourceFiles) {
    $relative = $file.FullName.Substring($sourceDir.Length).TrimStart([char]92, [char]47)
    $target = Join-Path $destinationDir $relative
    $targetParent = Split-Path -Parent $target
    if (-not (Test-Path -LiteralPath $targetParent)) {
        New-Item -ItemType Directory -Path $targetParent -Force | Out-Null
    }
    Copy-Item -LiteralPath $file.FullName -Destination $target -Force
}
Write-Output ('Installed focus skill: ' + $destinationDir)
