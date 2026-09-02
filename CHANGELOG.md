# Changelog

## 0.1.1 — 2026-08-27

- 从 `xuezheng627/zotero-literature-visualizer` `main`（commit `cc698cd1af730a9b3df6fe1a774652a72b1e8b8d`）更新 Visualizer 快照。
- 合并上游 v2 的引用网络、增量 NEW 摘要、阅读状态、分享卡、Zotero 回写、公共 dashboard 组件和合成示例。
- 保留本地 MRI 期刊注册表、ZH 中文翻译闸门、每刊最多 10 篇、授权浏览器 PDF 流程及 ScienceDirect 桥接扩展。
- 增加上游 `LICENSE`、`PRIVACY.md`、工作流参考文档和 `agents/openai.yaml`。

## 0.1.0 — 2026-08-26

- 首次发布统一 Literature Radar Suite。
- 收录 `literature-radar-hub`、`nature-academic-search`、`zotero-literature-visualizer`、`daily-literature-digest`、`paper-vault` 和 `paper-close-reading`。
- 统一入口包含 Gmail connector 与 Gmail MCP/应用发送路径检查。
- 安装/更新前备份已有 Skill，个人配置、PDF、Paper Vault 数据和连接器授权不进入套件。
- `sciencedirect-live-session-fetcher` 当前未安装，清单保留可选缺失状态和浏览器 fallback。
- 增加 `TargetSkillsRoot`，允许支持 `SKILL.md` 的非 Codex Agent 指定自己的 Skill 根目录；不支持 `SKILL.md` 的 Agent 需手动转换格式。
