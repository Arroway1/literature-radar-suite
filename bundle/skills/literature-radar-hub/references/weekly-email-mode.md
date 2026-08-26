# Weekly-email mode / 周报邮件模式

<!-- //============XJQ(本次修改：补充周报模式的依赖预检、多路 Gmail 发信检查、其他邮箱后备方案和可选归档说明)====================// -->

## Dependency preflight

Before fetching, check that `nature-academic-search` and
`daily-literature-digest` are installed. For a Gmail sender, inspect all
available send-capable Gmail paths at delivery time, including `gmail:gmail`
and any Gmail MCP/app send action; a Gmail read/search tool is not sufficient.
Record `sent`, `failed`, or `not-configured`.
`paper-vault` is optional and should be installed or used only when the user
requests a local archive. `sciencedirect-live-session-fetcher` is not required
for an abstract/metadata weekly report; if a user requests authorized
ScienceDirect full text, ask whether to install it, otherwise use the visible
browser fallback documented by `zotero-literature-visualizer`.

If a required skill is missing, pause and ask whether installation is allowed;
do not silently install or replace a Gmail connector or Gmail MCP/app path. If
an optional helper is missing, ask only when that optional operation is
requested and otherwise continue with the declared fallback.

<!-- //================XJQ(本次修改：补充周报模式的依赖预检、多路 Gmail 发信检查、其他邮箱后备方案和可选归档说明 END===============// -->

## Sender selection / 发件方式选择

Present these choices before the six-field report configuration:

1. **Gmail / Google Workspace**：检查所有可发信的 Gmail 路径，包括
   `gmail:gmail` 和 Gmail MCP/app 发信动作（例如运行时暴露的
   `mcp__codex_apps__gmail_send_email`）；Gmail 只读或搜索工具（read/search-only）不算发送器。
2. **其他邮箱**：合并 Outlook、Microsoft 365、QQ、163、企业邮箱和其他提供商，先检查对应 connector。
3. **只保存本地报告**：不发送邮件，也不需要邮件 connector。

The router records this choice with `delivery_provider` (`gmail`, `other`, or
`local_only`) and, for a non-Gmail provider, an optional `delivery_method`
(`provider_connector`, `smtp`, `manual_browser`, or `local_only`). An omitted
non-Gmail method intentionally remains `ask` until the user chooses a fallback.

If `其他邮箱` has no usable provider connector, offer exactly these fallbacks:

1. **SMTP**：使用安全 SMTP 适配器和用户授权凭据；不保存密码、授权码或 Cookie。
2. **浏览器手动发送**：使用用户当前明确授权的邮箱网页会话，不自动登录或无人值守点击发送。
3. **只保存本地报告**：保留完整 Markdown，并记录 `not-configured`，明确说明邮件未发送。

## Fetch

Read the project `daily-literature-digest.config.json` first. Preserve its
recipient, timezone, date window, output directory, sources, and keyword
groups. For a normal weekly window, run:

~~~powershell
& '<python>' '<daily-literature-digest>/scripts/daily_literature_digest.py' `
  --config '<workspace>/daily-literature-digest.config.json' `
  fetch --include-seen --lookback-days 7
~~~

If the user supplies explicit start/end dates, pass them instead of silently
changing the configured window. The fetch script writes open metadata JSON and
reports per-source errors; keep both artifacts.

The daily fetcher is provider-oriented. When the config names PubMed,
individual journals, Nature, Science, or OpenAlex explicitly, search those
sources through `nature-academic-search` first and merge its metadata into the
weekly report; do not claim that a source was searched only because it appears
in the JSON config.

## Evidence-bounded report

Write the complete Chinese Markdown in the configured output directory (use a
`weekly/` subdirectory when the config output is a shared root). For each item,
include title, date, journal/source, authors, DOI or official URL, matched
keywords, priority, evidence-bounded summary, and next action. State whether an
item is a preprint/not peer reviewed. For missing abstracts, write exactly the
equivalent of “仅依据题目判断；未推断方法、数据或结果”。Do not claim
full-text reading unless a visible authorized article/PDF was actually read.

If a source is unavailable, keep the report and state the source, error, and
successful fallback. An empty result also produces a Markdown report.

## Delivery route

After the local Markdown exists, use the route selected in the unified prompt:

- **Gmail / Google Workspace**: inspect all connected send-capable Gmail paths,
  including `gmail:gmail` and Gmail MCP/app send actions; use one available
  path, not a presumed tool name.
- **Other email**: check the provider-specific connector first. If none is
  available, offer SMTP, browser manual send, or local-only output.
- **Local-only**: do not send; retain the complete Markdown and record
  `not-configured` with an explicit note that delivery was intentionally
  skipped.

For SMTP, use only an explicitly available secure adapter and user-authorized
credentials; never store passwords, authorization codes, or cookies in JSON,
skill files, or logs. For browser manual send, use only the user's current
authorized session and do not automate login or unattended sending.

Record exactly one status: `sent`, `failed`, or `not-configured`.

Only then mark the digest state:

~~~powershell
& '<python>' '<daily-literature-digest>/scripts/daily_literature_digest.py' `
  --config '<workspace>/daily-literature-digest.config.json' `
  mark-success `
  --data-file '<DATA_JSON>' `
  --digest-file '<WEEKLY_MD>' `
  --email-status '<sent|failed|not-configured>'
~~~

## Optional Paper Vault archive

Use `paper-vault` only when the user asks for a local archive after the report.
Its default is full-text-safe: import High/Medium records only when a local PDF,
extracted full text, or visible authorized article text exists. Keep
title/abstract-only papers in the full-text inbox; do not infer objective,
method, result, usefulness, or next action from a title alone.

~~~powershell
& '<python>' '<paper-vault>/scripts/paper_vault.py' import-high `
  --vault-dir '<vault-dir>' `
  --digest-data-dir '<digest-data-dir>' `
  --config '<workspace>/daily-literature-digest.config.json' `
  --priority Medium --max-areas 5 --require-fulltext
~~~

## Automation notes

For a recurring task, include the exact workspace/config paths, Python path,
fetch command, recipient, sender route, language, timezone, output directory,
selected delivery-status rule, and a warning that the local Codex runner must
be awake. Keep the local Markdown even if email fails or local-only delivery is
selected.
