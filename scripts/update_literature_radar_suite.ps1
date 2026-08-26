# //============XJQ(本次修改：提供统一发布包的备份式更新入口)====================//
[CmdletBinding()]
param(
    [string]$BundleRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$CodexHome = (Join-Path $env:USERPROFILE '.codex'),
    # //============XJQ(本次修改：允许非 Codex Agent 通过更新入口指定 Skill 根目录)====================//
    [string]$TargetSkillsRoot = '',
    # //================XJQ(本次修改：允许非 Codex Agent 通过更新入口指定 Skill 根目录 END===============//
    [string]$BackupRoot = '',
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$syncScript = Join-Path $PSScriptRoot 'sync_literature_radar_suite.ps1'
& $syncScript -Operation update -BundleRoot $BundleRoot -CodexHome $CodexHome -TargetSkillsRoot $TargetSkillsRoot -BackupRoot $BackupRoot -DryRun:$DryRun
# //============XJQ(本次修改：避免严格模式下读取未设置的 LASTEXITCODE，改用 PowerShell 状态变量传递失败)====================//
if (-not $?) { exit 1 }
# //================XJQ(本次修改：避免严格模式下读取未设置的 LASTEXITCODE，改用 PowerShell 状态变量传递失败 END===============//
# //================XJQ(本次修改：提供统一发布包的备份式更新入口 END===============//
