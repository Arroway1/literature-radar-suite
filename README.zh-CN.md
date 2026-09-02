# Literature Radar Suite

这是一个可统一发布和更新的 MRI 文献工作流 Skill 套件。每个依赖仍保留独立目录，因此 `$paper-close-reading`、`$paper-vault` 等独立调用能力不会丢失；`literature-radar-hub` 负责统一入口、模式选择和依赖预检。

<!-- //============XJQ(本次修改：提供公开 GitHub 仓库的下载与更新入口)====================// -->
公开仓库：<https://github.com/Arroway1/literature-radar-suite>

新用户可以下载 ZIP，或执行：

```powershell
git clone https://github.com/Arroway1/literature-radar-suite.git
cd literature-radar-suite
& .\scripts\install_literature_radar_suite.ps1
```

后续更新：

```powershell
git pull --ff-only
& .\scripts\update_literature_radar_suite.ps1
```
<!-- //================XJQ(本次修改：提供公开 GitHub 仓库的下载与更新入口 END===============// -->

当前套件版本为 `0.1.1`。其中 `zotero-literature-visualizer` 已同步上游
`xuezheng627/zotero-literature-visualizer` 的 `main`（2026-08-27 快照），并保留本套件的 MRI 期刊注册表、ZH 中文翻译闸门、每刊最多 10 篇和授权浏览器扩展。

## 包含内容

当前套件包含：

- `literature-radar-hub`
- `nature-academic-search`
- `zotero-literature-visualizer`
- `daily-literature-digest`
- `paper-vault`
- `paper-close-reading`

Visualizer 同时包含上游 v2 的引用关系网络、增量 NEW 摘要、阅读状态、分享卡、Zotero 回写、公共 dashboard 组件和合成示例。

`sciencedirect-live-session-fetcher` 当前没有安装到本机，因此没有伪造占位目录；需要该全文路线时，依赖预检会提示安装，或使用 Visualizer 的授权浏览器 fallback。

## 安装

在套件根目录运行：

```powershell
& .\scripts\install_literature_radar_suite.ps1
```

如需指定 Codex 目录：

```powershell
& .\scripts\install_literature_radar_suite.ps1 `
  -CodexHome 'C:\Users\<用户名>\.codex'
```

安装目标是 `<CodexHome>\skills\` 下的并列 Skill 目录，不是 `literature-radar-hub\vendor\`。

## 其他 Agent

套件中的每个依赖都是独立的 `SKILL.md` 目录。对方如果使用支持
`SKILL.md` 的其他 Agent，可以把该 Agent 的 Skill 根目录显式传入：

```powershell
& .\scripts\install_literature_radar_suite.ps1 `
  -TargetSkillsRoot 'D:\OtherAgent\skills'
```

对方随后必须按照该 Agent 的规则重新加载 Skill。若该 Agent 不支持
`SKILL.md`，不能直接声称“安装成功”，需要把各目录转换成它支持的
rules、plugin 或 workflow 格式。Codex 专用的 `skill-installer`、
`mcp__codex_apps__gmail_send_email` 和 Gmail 授权不会随套件迁移。

`-CodexHome` 与 `-TargetSkillsRoot` 二选一；提供 `-TargetSkillsRoot` 时，
备份目录默认放在目标 Skill 根目录的旁边。

## 更新

如果套件由 Git 仓库发布，先更新套件源，再执行：

```powershell
git pull --ff-only
& .\scripts\update_literature_radar_suite.ps1
```

已有目标 Skill 会先备份到：

```text
<CodexHome>\skill-suite-backups\literature-radar-suite\<时间戳>\
```

可以先用 `-DryRun` 查看计划：

```powershell
& .\scripts\update_literature_radar_suite.ps1 -DryRun
```

## 不会同步的内容

以下内容必须由每个用户自己配置或授权：

- `daily-literature-digest.config.json`（邮箱、时区、关键词、来源和输出目录）
- Gmail connector 或 Gmail MCP 授权
- Outlook、QQ、163 或企业邮箱 connector
- 密码、授权码、Cookie、浏览器会话
- PDF、日报、Paper Vault 数据和本地研究资料

Gmail 发送器会在运行时检查 `gmail:gmail` 与可用的 Gmail MCP/应用发送动作；复制套件不会转移 Gmail 登录状态。
