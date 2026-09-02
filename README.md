# Literature Radar Suite

一个可安装、可更新、可迁移的文献检索、综述、可视化与精读 Skill 套件。

它将多个独立 Skill 组合发布，但不会把它们混成一个不可维护的文件。用户可以通过统一入口选择一个或多个能力，也可以直接调用某个独立 Skill。

## 快速开始

### Codex

~~~powershell
git clone https://github.com/Arroway1/literature-radar-suite.git
Set-Location literature-radar-suite
& .\scripts\install_literature_radar_suite.ps1
~~~

安装完成后，重启 Codex 或新建任务以刷新 Skill 索引。

### 其他 Agent

如果 Agent 支持读取 <code>SKILL.md</code>，可以指定它的 Skill 根目录：

~~~powershell
git clone https://github.com/Arroway1/literature-radar-suite.git
Set-Location literature-radar-suite
& .\scripts\install_literature_radar_suite.ps1 -TargetSkillsRoot 'D:\OtherAgent\skills'
~~~

<code>-CodexHome</code> 与 <code>-TargetSkillsRoot</code> 二选一。若 Agent 不支持 <code>SKILL.md</code>，需要把 <code>bundle\skills\</code> 下的目录转换为该 Agent 支持的 rules、plugin 或 workflow 格式。

## 套件包含什么

| 能力 | 适用场景 | 主要输出 |
|---|---|---|
| <code>literature-radar-hub</code> | 统一入口、依赖预检、模式选择 | 检索/可视化/邮件/归档/精读计划 |
| <code>nature-academic-search</code> | 多源学术检索和引用处理 | 规范化文献元数据、引用文件和来源状态 |
| <code>zotero-literature-visualizer</code> | 新主题检索或 Zotero 文献库可视化 | 中文综述、双语证据卡片、离线 dashboard |
| <code>daily-literature-digest</code> | 日报/周报和状态记录 | 中文 Markdown、来源错误记录、邮件状态 |
| <code>paper-vault</code> | 已提供 PDF/全文的本地归档 | 可搜索 Paper Vault 和全文待办箱 |
| <code>paper-close-reading</code> | 单篇或多篇论文精读 | Guided 逐节笔记或 Autonomous 完整精读记录 |

各目录都是独立 Skill；套件不是一个新的、需要额外调用的 Skill 名称。

## 如何使用

### 统一入口

~~~text
使用 $literature-radar-hub。
~~~

每次调用会先展示完整功能提示。用户可以多选功能，没有固定先后顺序；系统只询问所选功能缺少的配置。

### 生成综述和交互式 dashboard

~~~text
使用 $literature-radar-hub，选择 visualizer。

关键词：<填写关键词或关键词组>
日期：<填写开始日期> 至今
来源：<填写期刊、数据库或出版社>
数量上限：<可选>
输出目录：<填写目录>
~~~

也可以直接使用：

~~~text
使用 $zotero-literature-visualizer，
按指定关键词和日期范围检索文献，
生成中文综述、双语证据卡片和离线交互式 dashboard。
~~~

已有 Zotero 文献库时：

~~~text
读取我 Zotero 中带本地 PDF 的文献，
按主题和方法分类，生成中文综述与交互式 dashboard。
~~~

直接检索新主题不要求本地安装 Zotero；读取本地 Zotero 库或回写 Zotero 时，才需要 Zotero 本地数据/API 权限。

常见 Visualizer 输出：

~~~text
review-cn.md
review-bilingual.md
relationship-map.md
metadata/papers.json
dashboard-spec.json
literature-dashboard.html
~~~

### 生成日报或周报

~~~text
使用 $literature-radar-hub，选择 weekly-email。
~~~

报告字段缺失时会提示：

~~~text
日报配置：邮箱、时区、日期、来源、关键词、输出目录
~~~

对于 <code>weekly-email</code>，必须读取项目中的 <code>daily-literature-digest.config.json</code>。文件中的邮箱、时区、日期范围、来源、关键词组和输出目录是配置来源，不从浏览器状态猜测。

发送方式由用户选择：

1. Gmail/Google Workspace：检查 Gmail connector，以及可用的 Gmail MCP/app 发信动作；
2. 其他邮箱：先检查对应 provider connector；
3. 只保存本地报告：不发送邮件，也不需要邮箱 connector。

如果没有可用的其他邮箱 connector，提供三个后备方案：

1. 使用安全 SMTP 适配器；
2. 用户在已授权的邮箱网页会话中手动发送；
3. 只保存本地报告。

邮件状态只能记录为 <code>sent</code>、<code>failed</code> 或 <code>not-configured</code>，不能把生成本地文件误报为已发送。

### 使用 Paper Vault

~~~text
使用 $paper-vault，
将 <PDF目录> 下已提供的 PDF 归档，
只导入已经阅读过全文的文献，并生成可搜索 dashboard。
~~~

默认要求存在本地 PDF、文章全文或用户提供的全文文本。没有全文的文献会进入 <code>fulltext-inbox</code>，不会被伪造成完整论文卡片。

### 精读论文

Guided 模式：

~~~text
$paper-close-reading
精读这篇论文，按 Guided 模式逐节分析。
PDF 路径：<绝对路径>
~~~

Autonomous 模式：

~~~text
请用 paper-close-reading 以 Autonomous 模式完整精读这篇论文。
PDF 路径：<绝对路径>
~~~

Guided 模式每次分析一个章节或段落并等待用户继续；Autonomous 模式完成三遍完整阅读后一次性交付。

## 依赖预检

运行前会检查所选功能的依赖：

| 依赖 | 使用时机 | 缺少时的行为 |
|---|---|---|
| <code>nature-academic-search</code> | 新主题检索 | 先询问是否安装，不能静默跳过 |
| <code>zotero-literature-visualizer</code> | Visualizer | 暂停可视化分支并说明原因 |
| <code>daily-literature-digest</code> | 日报/周报 | 暂停邮件报告分支并说明原因 |
| <code>paper-vault</code> | 用户请求本地归档 | 仅在选择归档时检查 |
| <code>paper-close-reading</code> | 用户请求 PDF 精读 | 仅暂停精读分支 |
| Gmail/其他邮箱 connector | 用户选择邮件发送 | 检查实际可用的发信动作 |
| <code>sciencedirect-live-session-fetcher</code> | 明确请求 ScienceDirect 全文 | 当前未随套件提供，询问后再安装或使用可见浏览器降级流程 |

缺少依赖时不会假装已安装。安装第三方 Skill 或 connector 前必须得到用户许可。

## 证据和检索边界

- 优先使用官方学术来源和开放元数据，并记录每个来源的成功或失败状态；
- 按规范化 DOI 去重；无 DOI 时使用规范化标题、第一作者和标题词元相似度；
- 只依据标题、摘要和开放元数据总结，除非用户另行提供 PDF 或明确授权的文章页面；
- 没有摘要时必须说明“仅依据题目判断，未推断方法或结果”；
- 预印本必须标记“未同行评审”；
- 文献数量上限由用户在请求或配置中指定，不在公共 README 固定个人参数；
- 即使无结果或部分来源失败，也必须生成报告并记录限制。

## 更新套件

~~~powershell
Set-Location literature-radar-suite
git pull --ff-only
& .\scripts\update_literature_radar_suite.ps1
~~~

其他 Agent 更新时指定相同的目标目录：

~~~powershell
& .\scripts\update_literature_radar_suite.ps1 -TargetSkillsRoot 'D:\OtherAgent\skills'
~~~

更新前会备份已有 Skill。可以先预览：

~~~powershell
& .\scripts\update_literature_radar_suite.ps1 -DryRun
~~~

更新不会覆盖用户配置、PDF、Paper Vault 数据、密码、Cookie、浏览器会话或邮箱授权。

## 隐私和安全

本仓库只发布 Skill、脚本、说明和合成示例，不发布：

- 日报配置文件；
- PDF、全文提取、日报和 Paper Vault 数据；
- Zotero 数据库、个人笔记和本地绝对路径；
- 密码、授权码、API key、Cookie 或浏览器配置；
- Gmail、QQ、163、Outlook 或企业邮箱授权状态。

禁止无人值守登录、自动处理 CAPTCHA、绕过付费墙或构造隐藏付费 PDF 地址。全文访问只使用用户明确授权的可见浏览器会话或用户手动提供的文件。

本地日报自动化依赖电脑和 Agent runner 处于运行状态；电脑休眠或 runner 停止时，自动任务可能不会执行。

## 验证和故障排查

安装后若看不到 Skill：

1. 重启 Agent 或新建任务；
2. 确认目标目录下存在对应的 <code>SKILL.md</code>；
3. 运行相应 Skill 的 <code>quick_validate.py</code>；
4. 检查依赖预检输出，不要手动假设 connector 已连接。

公开发布前建议运行：

~~~powershell
& .\bundle\skills\literature-radar-hub\scripts\quick_validate.py
& .\bundle\skills\zotero-literature-visualizer\scripts\quick_validate.py .\bundle\skills\zotero-literature-visualizer
~~~

## 版本和来源

<code>bundle-manifest.json</code> 是套件组成、版本和上游快照的记录；更新组件时应同步更新该文件并运行验证脚本。

## 致谢

<sub>
本套件由 Arroway1 负责集成、兼容性扩展和发布。
其中的
<a href="https://github.com/xuezheng627/zotero-literature-visualizer">
zotero-literature-visualizer
</a>
来自 xuezheng627 的公开项目。
其余内置 Skill（nature-academic-search、daily-literature-digest、paper-vault、paper-close-reading）的原作者、许可证和修改历史，以各自目录中的 README.md、SKILL.md、LICENSE 或 CHANGELOG.md 为准。
本仓库仅做组合发布，不改变任何上游作者的版权和许可证。
</sub>
