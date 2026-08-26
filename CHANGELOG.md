# Changelog

## 0.1.0 — 2026-08-26

- 首次发布统一 Literature Radar Suite。
- 收录 `literature-radar-hub`、`nature-academic-search`、`zotero-literature-visualizer`、`daily-literature-digest`、`paper-vault` 和 `paper-close-reading`。
- 统一入口包含 Gmail connector 与 Gmail MCP/应用发送路径检查。
- 安装/更新前备份已有 Skill，个人配置、PDF、Paper Vault 数据和连接器授权不进入套件。
- `sciencedirect-live-session-fetcher` 当前未安装，清单保留可选缺失状态和浏览器 fallback。
- 增加 `TargetSkillsRoot`，允许支持 `SKILL.md` 的非 Codex Agent 指定自己的 Skill 根目录；不支持 `SKILL.md` 的 Agent 需手动转换格式。
