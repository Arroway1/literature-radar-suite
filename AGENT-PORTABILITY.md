# Agent portability / Agent 兼容边界

## 可以直接复用的部分

`bundle/skills/` 中的每个目录都包含独立的 `SKILL.md`、references 和 scripts。
支持 Agent Skills 或相同目录契约的 Agent，可以将所需目录复制到自己的 Skill 根目录。
`bundle-manifest.json` 是组件、模式角色和缺失可选依赖的清单。

## Codex 适配

默认安装目标是：

```text
<CodexHome>\skills\
```

使用 `scripts/install_literature_radar_suite.ps1` 或
`scripts/update_literature_radar_suite.ps1`。Codex 的 `skill-installer` 只适合
安装单个 Skill；整个套件使用本目录的同步脚本。

## 其他支持 SKILL.md 的 Agent

把目标 Agent 的 Skill 根目录传给 `-TargetSkillsRoot`：

```powershell
& .\scripts\install_literature_radar_suite.ps1 `
  -TargetSkillsRoot 'D:\OtherAgent\skills'
```

同步脚本只复制并列 Skill 目录；目标 Agent 的加载、重载、新会话和工具映射
仍由目标 Agent 自己负责。

## 不支持 SKILL.md 的 Agent

不能直接安装。请将每个 Skill 的 `SKILL.md` 转换为目标 Agent 的 rules、plugin
或 workflow 格式，并按目标 Agent 的方式注册 scripts/references。不要把
“文件已复制”误报为“目标 Agent 已加载”。

## 运行时隔离

Gmail connector/MCP、Zotero API、浏览器会话、邮箱凭据、Cookie、日报 JSON、PDF
和 Paper Vault 数据都属于用户或 Agent 的运行时状态，不在套件内，也不会跨 Agent
同步。目标 Agent 需要提供自己的检索、发送和本地文件访问能力；没有对应能力时
应使用公开来源、SMTP/手动发送或只保存本地报告的 fallback。
