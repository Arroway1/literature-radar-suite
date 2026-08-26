# //============XJQ(本次修改：实现 Literature Radar Suite 的清单校验、备份和并列 Skill 同步)====================//
[CmdletBinding()]
param(
    [ValidateSet('install', 'update')]
    [string]$Operation = 'install',
    [string]$BundleRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$CodexHome = (Join-Path $env:USERPROFILE '.codex'),
    # //============XJQ(本次修改：允许非 Codex Agent 显式指定其 Skill 根目录)====================//
    [string]$TargetSkillsRoot = '',
    # //================XJQ(本次修改：允许非 Codex Agent 显式指定其 Skill 根目录 END===============//
    [string]$BackupRoot = '',
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# //============XJQ(本次修改：提供安全路径、清单和 Skill 快照校验)====================//
function Get-FullPath {
    param([Parameter(Mandatory)][string]$Path)
    return [System.IO.Path]::GetFullPath((Resolve-Path -LiteralPath $Path).Path)
}

function Assert-ChildPath {
    param(
        [Parameter(Mandatory)][string]$Candidate,
        [Parameter(Mandatory)][string]$Parent,
        [Parameter(Mandatory)][string]$Label
    )
    $candidateFull = [System.IO.Path]::GetFullPath($Candidate)
    $parentFull = [System.IO.Path]::GetFullPath($Parent).TrimEnd([System.IO.Path]::DirectorySeparatorChar) + [System.IO.Path]::DirectorySeparatorChar
    if (-not $candidateFull.StartsWith($parentFull, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "$Label escapes its allowed root: $Candidate"
    }
    return $candidateFull
}

function Read-BundleManifest {
    param([Parameter(Mandatory)][string]$Root)
    $manifestPath = Join-Path $Root 'bundle-manifest.json'
    if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) {
        throw "bundle-manifest.json not found under $Root"
    }
    $manifest = Get-Content -LiteralPath $manifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($manifest.suite_name -ne 'literature-radar-suite') {
        throw "Unsupported suite_name: $($manifest.suite_name)"
    }
    if (-not $manifest.included -or $manifest.included.Count -eq 0) {
        throw 'Manifest has no included Skill entries'
    }
    return $manifest
}

function Assert-SkillEntry {
    param(
        [Parameter(Mandatory)]$Entry,
        [Parameter(Mandatory)][string]$BundleRoot,
        [Parameter(Mandatory)][string]$SkillsRoot
    )
    if ($Entry.name -notmatch '^[A-Za-z0-9][A-Za-z0-9._-]*$') {
        throw "Invalid Skill name: $($Entry.name)"
    }
    $relative = [string]$Entry.path
    if ([System.IO.Path]::IsPathRooted($relative)) {
        throw "Skill path must be relative: $relative"
    }
    $source = Assert-ChildPath -Candidate (Join-Path $BundleRoot $relative) -Parent $SkillsRoot -Label "Skill $($Entry.name)"
    if (-not (Test-Path -LiteralPath $source -PathType Container)) {
        throw "Skill directory missing: $source"
    }
    if (-not (Test-Path -LiteralPath (Join-Path $source 'SKILL.md') -PathType Leaf)) {
        throw "SKILL.md missing for $($Entry.name): $source"
    }
    return $source
}
# //================XJQ(本次修改：提供安全路径、清单和 Skill 快照校验 END===============//

# //============XJQ(本次修改：实现备份、暂存复制和状态输出，避免覆盖用户现有 Skill)====================//
function Sync-SkillSnapshot {
    param(
        [Parameter(Mandatory)][string]$Name,
        [Parameter(Mandatory)][string]$Source,
        [Parameter(Mandatory)][string]$TargetRoot,
        [Parameter(Mandatory)][string]$BackupRoot,
        [Parameter(Mandatory)][string]$Operation,
        [Parameter(Mandatory)][bool]$DryRun
    )
    $target = Join-Path $TargetRoot $Name
    $staging = Join-Path $TargetRoot ('.' + $Name + '.staging-' + [Guid]::NewGuid().ToString('N'))
    $backup = Join-Path $BackupRoot $Name
    $hadExisting = Test-Path -LiteralPath $target

    if ($DryRun) {
        if ($hadExisting) {
            Write-Output ("{0}: would-backup -> {1}" -f $Name, $backup)
        }
        Write-Output ("{0}: would-{1}" -f $Name, $Operation)
        return
    }

    New-Item -ItemType Directory -Path $staging -Force | Out-Null
    try {
        Get-ChildItem -LiteralPath $Source -Force | ForEach-Object {
            Copy-Item -LiteralPath $_.FullName -Destination $staging -Recurse -Force
        }
        if (-not (Test-Path -LiteralPath (Join-Path $staging 'SKILL.md') -PathType Leaf)) {
            throw "Staged Skill is missing SKILL.md: $Name"
        }
        if ($hadExisting) {
            New-Item -ItemType Directory -Path $BackupRoot -Force | Out-Null
            Move-Item -LiteralPath $target -Destination $backup -Force
        }
        Move-Item -LiteralPath $staging -Destination $target
        if ($hadExisting) {
            Write-Output ("{0}: backed-up and {1}" -f $Name, $Operation)
        } else {
            Write-Output ("{0}: {1}" -f $Name, $Operation)
        }
    } catch {
        if (Test-Path -LiteralPath $staging) {
            Remove-Item -LiteralPath $staging -Recurse -Force -ErrorAction SilentlyContinue
        }
        throw
    }
}
# //================XJQ(本次修改：实现备份、暂存复制和状态输出，避免覆盖用户现有 Skill END===============//

# //============XJQ(本次修改：执行统一清单同步并隔离个人配置、连接器和全文数据)====================//
$resolvedBundleRoot = Get-FullPath -Path $BundleRoot
$manifest = Read-BundleManifest -Root $resolvedBundleRoot
$manifestSkillsRoot = Get-FullPath -Path (Join-Path $resolvedBundleRoot $manifest.bundle_root)
$resolvedCodexHome = [System.IO.Path]::GetFullPath($CodexHome)
# //============XJQ(本次修改：优先使用通用 Agent 的显式目标目录，否则保持 Codex 默认路径)====================//
$targetRoot = if ([string]::IsNullOrWhiteSpace($TargetSkillsRoot)) {
    Join-Path $resolvedCodexHome 'skills'
} else {
    [System.IO.Path]::GetFullPath($TargetSkillsRoot)
}
# //================XJQ(本次修改：优先使用通用 Agent 的显式目标目录，否则保持 Codex 默认路径 END===============//
New-Item -ItemType Directory -Path $targetRoot -Force | Out-Null

if ([string]::IsNullOrWhiteSpace($BackupRoot)) {
    # //============XJQ(本次修改：让非 Codex Agent 的默认备份跟随其目标 Skill 根目录)====================//
    $backupBase = if ([string]::IsNullOrWhiteSpace($TargetSkillsRoot)) { $resolvedCodexHome } else { Split-Path -Parent $targetRoot }
    $BackupRoot = Join-Path $backupBase ('skill-suite-backups\literature-radar-suite\' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
    # //================XJQ(本次修改：让非 Codex Agent 的默认备份跟随其目标 Skill 根目录 END===============//
} else {
    $BackupRoot = [System.IO.Path]::GetFullPath($BackupRoot)
}

$results = @()
foreach ($entry in $manifest.included) {
    $source = Assert-SkillEntry -Entry $entry -BundleRoot $resolvedBundleRoot -SkillsRoot $manifestSkillsRoot
    Sync-SkillSnapshot -Name $entry.name -Source $source -TargetRoot $targetRoot -BackupRoot $BackupRoot -Operation $Operation -DryRun:$DryRun
    $results += $entry.name
}

foreach ($missing in @($manifest.optional_missing)) {
    Write-Output ("{0}: missing-optional ({1})" -f $missing.name, $missing.status)
}

Write-Output ("suite {0} {1}; synchronized {2} Skill(s); backup root: {3}" -f $manifest.suite_version, $Operation, $results.Count, $BackupRoot)
# //================XJQ(本次修改：执行统一清单同步并隔离个人配置、连接器和全文数据 END===============//

# //================XJQ(本次修改：实现 Literature Radar Suite 的清单校验、备份和并列 Skill 同步 END===============//
