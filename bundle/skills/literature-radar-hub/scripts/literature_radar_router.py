# //============XJQ(本次修改：实现统一文献雷达的模式路由、配置校验和可执行计划输出）====================//
"""Build safe execution plans for the unified literature-radar skill.

The router deliberately does not fetch papers or send email. It validates the
user configuration and tells Codex which installed implementation skill and
commands to use, keeping network retrieval and the selected delivery route
visible and confirmable at the orchestration layer.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
from copy import deepcopy
from pathlib import Path
from typing import Any


MODES = ("visualizer", "weekly-email")
EMAIL_STATUS_VALUES = ["sent", "failed", "not-configured"]

# //============XJQ(本次修改：增加通用发件路线枚举，支持 Gmail/MCP、其他邮箱和仅本地报告)====================//
DELIVERY_PROVIDERS = ("gmail", "other", "local_only")
OTHER_DELIVERY_METHODS = ("provider_connector", "smtp", "manual_browser", "local_only")
GMAIL_SEND_PATHS = ("gmail:gmail", "gmail:mcp")
DELIVERY_PROMPT = "\n".join(
    [
        "发件方式：",
        "- Gmail / Google Workspace：检查 Gmail connector 和 Gmail MCP/应用发送动作；只读/搜索工具不算发件通道。",
        "- 其他邮箱（Outlook、Microsoft 365、QQ、163、企业邮箱或其他）：先检查对应 connector；若不可用，选择 SMTP、浏览器手动发送或只保存本地报告。",
        "- 仅保存本地报告：不需要任何邮箱 connector，也不要求收件人地址。",
    ]
)
# //================XJQ(本次修改：增加通用发件路线枚举，支持 Gmail/MCP、其他邮箱和仅本地报告 END===============//

# //============XJQ(本次修改：定义统一的日报配置询问模板和 MRI 参考参数)====================//
DEFAULT_CONFIG_PROMPT = "\n".join(
    [
        "\u65e5\u62a5\u914d\u7f6e：",
        "- \u90ae\u7bb1：\u8bf7\u8865\u5145",
        "- \u65f6\u533a：\u8bf7\u8865\u5145",
        "- \u65e5\u671f：\u53c2\u8003 2026-01-01 \u81f3\u8fd0\u884c\u65e5",
        "- \u6765\u6e90：\u53c2\u8003 PubMed、Crossref、OpenAlex、arXiv、Nature、Science；Visualizer \u53ef\u52a0 MRM、NeuroImage、TMI、MIA、Radiology、Medical Physics、npj Digital Medicine",
        "- \u5173\u952e\u8bcd：\u53c2\u8003 MRI、AI、ASL、BBB、VASO、PVS、LIVER、diffusion-prepared、Hemodynamics、neuroimaging",
        "- \u8f93\u51fa\u76ee\u5f55：\u8bf7\u8865\u5145",
        "\u8bf7\u7528\u6237\u8865\u5145\u90ae\u7bb1、\u65f6\u533a\u548c\u8f93\u51fa\u76ee\u5f55；\u53ef\u76f4\u63a5\u91c7\u7528\u4e0a\u8ff0\u65e5\u671f、\u6765\u6e90\u548c\u5173\u952e\u8bcd\u53c2\u8003\u503c。",
    ]
)
REFERENCE_DEFAULTS: dict[str, Any] = {
    "email": {"value": "", "user_supplied": True},
    "timezone": {"value": "", "user_supplied": True},
    "date": {"from": "2026-01-01", "to": "runtime_date", "user_supplied": False},
    "sources": ["PubMed", "Crossref", "OpenAlex", "arXiv", "Nature", "Science"],
    "visualizer_journals": [
        "MRM",
        "NeuroImage",
        "TMI",
        "MIA",
        "Radiology",
        "Medical Physics",
        "npj Digital Medicine",
    ],
    "keywords": [
        "MRI",
        "AI",
        "ASL",
        "BBB",
        "VASO",
        "PVS",
        "LIVER",
        "diffusion-prepared",
        "Hemodynamics",
        "neuroimaging",
    ],
    "output_dir": {"value": "", "user_supplied": True},
}
# //================XJQ(本次修改：定义统一的日报配置询问模板和 MRI 参考参数 END===============//

# //============XJQ(本次修改：建立统一入口依赖矩阵、可用性探测与安装询问所需的元数据)====================//
DEPENDENCY_SPECS: dict[str, dict[str, Any]] = {
    "nature-academic-search": {
        "role": "required_search",
        "kind": "skill",
        "skill_dir": "nature-academic-search",
        "required_for": ["visualizer", "weekly-email"],
        "installable": True,
        "install_hint": "使用 skill-installer 安装 nature-academic-search。",
    },
    "zotero-literature-visualizer": {
        "role": "required_visualizer",
        "kind": "skill",
        "skill_dir": "zotero-literature-visualizer",
        "required_for": ["visualizer"],
        "installable": True,
        "install_hint": "使用 skill-installer 安装 zotero-literature-visualizer。",
    },
    "daily-literature-digest": {
        "role": "required_weekly_email",
        "kind": "skill",
        "skill_dir": "daily-literature-digest",
        "required_for": ["weekly-email"],
        "installable": True,
        "install_hint": "使用 skill-installer 安装 daily-literature-digest。",
    },
    "gmail:gmail": {
        "role": "required_delivery_when_connected",
        "kind": "connector",
        "required_for": ["weekly-email"],
        "installable": False,
        "install_hint": "检查 Gmail connector 是否已连接；不可用时记录 not-configured 或 failed。",
    },
    # //============XJQ(本次修改：登记 Gmail MCP/应用发送动作作为 Gmail connector 的可替代发件路径)====================//
    "gmail:mcp": {
        "role": "alternate_gmail_delivery",
        "kind": "connector",
        "required_for": [],
        "optional_for": ["weekly-email"],
        "installable": False,
        "install_hint": "检查运行时是否暴露可发送 Gmail 的 MCP/应用动作；仅搜索或读取 Gmail 的工具不满足发送要求。",
    },
    # //================XJQ(本次修改：登记 Gmail MCP/应用发送动作作为 Gmail connector 的可替代发件路径 END===============//
    "paper-vault": {
        "role": "optional_archive",
        "kind": "skill",
        "skill_dir": "paper-vault",
        "required_for": [],
        "optional_for": ["visualizer", "weekly-email"],
        "installable": True,
        "install_hint": "只有用户需要本地全文归档时才安装 paper-vault。",
    },
    "sciencedirect-live-session-fetcher": {
        "role": "optional_sciencedirect_fulltext",
        "kind": "skill",
        "skill_dir": "sciencedirect-live-session-fetcher",
        "required_for": [],
        "optional_for": ["visualizer", "weekly-email"],
        "installable": True,
        "install_hint": "仅在用户授权 ScienceDirect/Elsevier 可见浏览器全文任务时询问安装。",
        "fallback": "使用 zotero-literature-visualizer/scripts/browser_pdf_downloader.py 的可见授权浏览器流程。",
    },
}
# //================XJQ(本次修改：建立统一入口依赖矩阵、可用性探测与安装询问所需的元数据 END===============//


class ConfigError(ValueError):
    """Raised when the configured literature-radar inputs are unsafe or incomplete."""


# //============XJQ(本次修改：在执行模式前探测本地 skill 与连接器，并生成缺失依赖询问信息)====================//
def _default_skill_root() -> Path:
    """Return the shared Codex skill root when running from the installed hub."""
    return Path(__file__).resolve().parents[2]


def build_dependency_matrix(skill_root: str | Path | None = None) -> dict[str, dict[str, Any]]:
    """Probe installed skills and annotate connector-managed dependencies."""
    root = Path(skill_root).expanduser() if skill_root else _default_skill_root()
    matrix: dict[str, dict[str, Any]] = {}
    for name, spec in DEPENDENCY_SPECS.items():
        item = dict(spec)
        if spec.get("kind") == "skill":
            skill_dir = root / str(spec["skill_dir"])
            item["availability"] = "installed" if (skill_dir / "SKILL.md").is_file() else "not-installed"
        else:
            item["availability"] = "connector-managed"
            item["runtime_check_required"] = True
        matrix[name] = item
    return matrix


# //============XJQ(本次修改：解析用户选择的 Gmail、其他邮箱或仅本地报告路线)====================//
def _delivery_settings(config: dict[str, Any]) -> tuple[str, str]:
    """Return normalized delivery provider/method without collecting secrets."""
    mail_delivery = config.get("mail_delivery") if isinstance(config.get("mail_delivery"), dict) else {}
    raw_provider = config.get("delivery_provider") or mail_delivery.get("provider") or "gmail"
    provider_aliases = {
        "gmail_connector": "gmail",
        "gmail_mcp": "gmail",
        "google": "gmail",
        "other_email": "other",
        "provider_connector": "other",
        "local": "local_only",
        "local-report": "local_only",
    }
    provider = provider_aliases.get(str(raw_provider).strip().lower(), str(raw_provider).strip().lower())
    if provider not in DELIVERY_PROVIDERS:
        raise ConfigError(
            "delivery_provider must be one of gmail, other, local_only; "
            f"got {raw_provider!r}"
        )
    raw_method = config.get("delivery_method") or mail_delivery.get("method") or ""
    method = str(raw_method).strip().lower()
    if provider == "gmail":
        # The runtime checks both Gmail paths; this value is descriptive, not a credential.
        method = method or "gmail_connector_or_mcp"
        if method not in {"gmail_connector_or_mcp", "gmail_connector", "gmail_mcp"}:
            raise ConfigError(
                "delivery_method for Gmail must be gmail_connector_or_mcp, "
                "gmail_connector, or gmail_mcp"
            )
    elif provider == "local_only":
        method = "local_only"
    else:
        if method and method not in OTHER_DELIVERY_METHODS:
            raise ConfigError(
                "delivery_method for other email must be provider_connector, smtp, "
                "manual_browser, or local_only"
            )
        # An absent method intentionally means the user still needs to choose a fallback.
        method = method or "ask"
    return provider, method
# //================XJQ(本次修改：解析用户选择的 Gmail、其他邮箱或仅本地报告路线 END===============//


def dependency_check(
    mode: str,
    matrix: dict[str, dict[str, Any]],
    delivery_provider: str = "gmail",
) -> dict[str, Any]:
    """Classify missing dependencies and describe the selected delivery alternatives."""
    # //============XJQ(本次修改：保留原有按模式收集依赖的逻辑，并按发件路线解除无关 Gmail 要求)====================//
    required = [name for name, item in matrix.items() if mode in item.get("required_for", [])]
    optional = [name for name, item in matrix.items() if mode in item.get("optional_for", [])]
    # //================XJQ(本次修改：保留原有按模式收集依赖的逻辑，并按发件路线解除无关 Gmail 要求 END===============//
    if mode == "weekly-email" and delivery_provider != "gmail":
        required = [name for name in required if name not in GMAIL_SEND_PATHS]
        optional = [name for name in optional if name not in GMAIL_SEND_PATHS]
    if mode == "weekly-email" and delivery_provider == "gmail":
        # gmail:gmail is kept in required for backward-compatible visibility;
        # gmail:mcp is the runtime alternative and is listed explicitly below.
        required = [name for name in required if name in set(GMAIL_SEND_PATHS) or name != "gmail:mcp"]
    missing_required = [name for name in required if matrix[name]["availability"] == "not-installed"]
    missing_optional = [name for name in optional if matrix[name]["availability"] == "not-installed"]
    missing = missing_required + missing_optional
    if missing:
        installable = [name for name in missing if matrix[name].get("installable")]
        user_prompt = (
            "检测到以下依赖未安装：" + ", ".join(missing) + "。是否允许安装？"
            "必需依赖缺失时需先暂停当前模式；可选依赖可选择继续并使用 fallback。"
        )
    else:
        installable = []
        user_prompt = "依赖矩阵检查通过；无需安装询问。"
    if mode == "weekly-email" and delivery_provider == "gmail":
        user_prompt += " Gmail 发件需运行时检查 gmail:gmail 与 gmail:mcp，任一可发送路径可用即可；只读/搜索工具不算发送通道。"
    elif mode == "weekly-email" and delivery_provider == "other":
        user_prompt += " 其他邮箱先检查 provider connector；没有时必须让用户在 SMTP、浏览器手动发送、只保存本地报告中选择。"
    elif mode == "weekly-email" and delivery_provider == "local_only":
        user_prompt += " 已选择只保存本地报告，不检查或调用邮箱 connector。"
    delivery_checks = []
    if mode == "weekly-email" and delivery_provider == "gmail":
        delivery_checks = list(GMAIL_SEND_PATHS)
    elif mode == "weekly-email" and delivery_provider == "other":
        delivery_checks = ["provider_connector"]
    return {
        "mode": mode,
        "delivery_provider": delivery_provider,
        "required": required,
        "optional": optional,
        "delivery_alternatives": list(GMAIL_SEND_PATHS) if mode == "weekly-email" and delivery_provider == "gmail" else [],
        "delivery_checks": delivery_checks,
        "missing_required": missing_required,
        "missing_optional": missing_optional,
        "install_candidates": installable,
        "must_pause_before_execution": bool(missing_required),
        "user_prompt": user_prompt,
    }
# //================XJQ(本次修改：在执行模式前探测本地 skill 与连接器，并生成缺失依赖询问信息 END===============//


def _date_value(config: dict[str, Any], *keys: str, default: str = "") -> str:
    for key in keys:
        value = str(config.get(key) or "").strip()
        if value:
            candidate = value[:10]
            try:
                return dt.date.fromisoformat(candidate).isoformat()
            except ValueError as exc:
                raise ConfigError(f"{key} must be an ISO date, got {value!r}") from exc
    return default


def _output_dir(config: dict[str, Any], config_path: str | Path) -> str:
    raw = str(config.get("output_dir") or "literature-radar-output").strip()
    path = Path(raw)
    if not path.is_absolute() and config_path:
        path = Path(config_path).resolve().parent / path
    return str(path)


def _source_labels(config: dict[str, Any]) -> list[str]:
    values = config.get("sources") or config.get("publishers") or []
    if isinstance(values, str):
        return [values]
    labels: list[str] = []
    for value in values if isinstance(values, list) else []:
        if isinstance(value, dict):
            label = str(value.get("display") or value.get("name") or value.get("key") or "").strip()
        else:
            label = str(value).strip()
        if label:
            labels.append(label)
    return labels


def _keyword_labels(config: dict[str, Any]) -> list[str]:
    groups = config.get("keyword_groups") or config.get("keywords") or []
    if isinstance(groups, dict):
        groups = [{"label": key, "terms": value} for key, value in groups.items()]
    labels: list[str] = []
    for group in groups if isinstance(groups, list) else []:
        if isinstance(group, dict):
            label = str(group.get("label") or group.get("name") or "").strip()
            terms = group.get("terms") or group.get("keywords") or []
            if not label and terms:
                label = ", ".join(str(term).strip() for term in terms if str(term).strip())
        else:
            label = str(group).strip()
        if label:
            labels.append(label)
    return labels


def _validate_common(config: dict[str, Any], config_path: str | Path) -> dict[str, Any]:
    if not isinstance(config, dict):
        raise ConfigError("configuration must be a JSON object")
    sources = _source_labels(config)
    keywords = _keyword_labels(config)
    if not sources:
        raise ConfigError("configuration must specify sources or publishers")
    if not keywords:
        raise ConfigError("configuration must specify keyword_groups or keywords")
    today = dt.date.today().isoformat()
    start = _date_value(config, "start_date", "from_date", default=today)
    end = _date_value(config, "to_date", "until_date", default=today)
    if start > end:
        raise ConfigError(f"date range is reversed: {start} > {end}")
    return {
        "config_path": str(Path(config_path).resolve()) if config_path else "",
        "output_dir": _output_dir(config, config_path),
        "sources": sources,
        "keyword_labels": keywords,
        "from_date": start,
        "to_date": end,
        "timezone": str(config.get("timezone") or "Asia/Shanghai"),
        "language": str(config.get("language") or "zh-CN"),
        "topic": str(config.get("topic") or " / ".join(keywords)),
        # //============XJQ(本次修改：把默认日报配置提示和参考值加入两种模式的公共计划字段)====================//
        "config_prompt": DEFAULT_CONFIG_PROMPT,
        "reference_defaults": deepcopy(REFERENCE_DEFAULTS),
        # //============XJQ(本次修改：把通用发件方式提示加入计划，避免默认把邮箱解释为 Gmail connector)====================//
        "delivery_prompt": DELIVERY_PROMPT,
        # //================XJQ(本次修改：把通用发件方式提示加入计划，避免默认把邮箱解释为 Gmail connector END===============//
        # //================XJQ(本次修改：把默认日报配置提示和参考值加入两种模式的公共计划字段 END===============//
    }


def build_plan(mode: str, config: dict[str, Any], config_path: str | Path = "", max_per_journal: int | None = None) -> dict[str, Any]:
    """Return a validated plan for one of the two user-facing modes."""
    if mode not in MODES:
        raise ConfigError(f"mode must be one of {', '.join(MODES)}")
    common = _validate_common(config, config_path)
    # //============XJQ(本次修改：把依赖矩阵和执行前检查注入 visualizer/weekly-email 计划)====================//
    dependency_matrix = build_dependency_matrix()
    # //============XJQ(本次修改：在周报模式解析发件路线，使 Gmail connector 与 Gmail MCP 成为可替代路径)====================//
    delivery_provider, delivery_method = (
        _delivery_settings(config) if mode == "weekly-email" else ("not-applicable", "not-applicable")
    )
    dependency_result = dependency_check(mode, dependency_matrix, delivery_provider)
    # //================XJQ(本次修改：在周报模式解析发件路线，使 Gmail connector 与 Gmail MCP 成为可替代路径 END===============//
    # //================XJQ(本次修改：把依赖矩阵和执行前检查注入 visualizer/weekly-email 计划 END===============//
    if mode == "visualizer":
        cap = int(max_per_journal if max_per_journal is not None else config.get("max_papers_per_journal", 10))
        if cap < 1:
            raise ConfigError("max_papers_per_journal must be at least 1")
        run_dir = str(Path(common["output_dir"]) / f"literature-visualizer-{common['to_date']}")
        return {
            **common,
            "mode": mode,
            "dependency_matrix": dependency_matrix,
            "dependency_check": dependency_result,
            "run_dir": run_dir,
            "max_papers_per_journal": cap,
            "required_actions": [
                "Use nature-academic-search multi-source-search (MCP first; PubMed first for biomedical topics; Crossref/OpenAlex/arXiv supplement; record failures).",
                "Use zotero-literature-visualizer to collect/classify MRI or Zotero records and render the interactive dashboard.",
                f"Run cap_journal_papers.py with --max-per-journal {cap} after date/MRI-context filtering and deduplication.",
                "Run translate_dashboard_zh.py so every details[*].zh field is Chinese while details[*].en remains the evidence layer.",
                "Run build_literature_dashboard.py and verify ranks, journal counts, CJK ZH fields, DOI links, and no placeholders.",
            ],
            "safety": [
                "Use title, abstract, and open metadata unless the user explicitly authorizes a full-text follow-up.",
                "Do not store passwords/cookies or perform unattended publisher login/paywall bypass.",
                "Mark preprints as not peer reviewed and state title-only limits when abstracts are absent.",
            ],
        }

    # //============XJQ(本次修改：保留旧的收件人校验意图，并允许仅本地报告不填写收件人)====================//
    recipient = str(config.get("recipient_email") or config.get("mailto") or "").strip()
    # //================XJQ(本次修改：保留旧的收件人校验意图，并允许仅本地报告不填写收件人 END===============//
    if delivery_provider != "local_only" and delivery_method != "local_only" and not recipient:
        raise ConfigError(
            "weekly-email mode requires recipient_email (or mailto) unless "
            "delivery_provider=local_only or delivery_method=local_only"
        )
    daily_script = "<daily-literature-digest>/scripts/daily_literature_digest.py"
    fetch = f"<python> {daily_script} --config {common['config_path']} fetch --include-seen --lookback-days 7"
    delivery_options = {
        "gmail": ["gmail_connector", "gmail_mcp"],
        "other": list(OTHER_DELIVERY_METHODS),
        "local_only": ["local_only"],
    }[delivery_provider]
    delivery_selection_required = delivery_provider == "other" and delivery_method == "ask"
    return {
        **common,
        "mode": mode,
        "dependency_matrix": dependency_matrix,
        "dependency_check": dependency_result,
        "recipient_email": recipient,
        "delivery_provider": delivery_provider,
        "delivery_method": delivery_method,
        "delivery_options": delivery_options,
        "delivery_selection_required": delivery_selection_required,
        "weekly_report_dir": str(Path(common["output_dir"]) / "weekly"),
        "email_status_values": EMAIL_STATUS_VALUES,
        "paper_vault_is_optional": True,
        "required_actions": [
            "Use nature-academic-search multi-source-search for the weekly discovery route; use PubMed first for biomedical records and Crossref/OpenAlex/arXiv as supplements.",
            f"Run the daily-literature-digest fetch command: {fetch}",
            "Write the complete Chinese weekly Markdown from title/abstract/open metadata; label arXiv/preprints and do not infer missing-abstract methods or results.",
            "Resolve the selected delivery route: Gmail checks gmail:gmail and Gmail MCP/app send actions (either send-capable path is sufficient); other email checks its provider connector then offers SMTP, browser manual send, or local-only; local-only does not send.",
            "Run mark-success only after the Markdown file exists and pass the recorded email status.",
        ],
        "fetch_command": fetch,
        "source_guard": "The daily fetcher is provider-oriented; apply an explicit PubMed, individual-journal, Nature, Science, or OpenAlex source list through nature-academic-search first, then merge its metadata into the weekly report. Do not claim an unsupported source was searched merely because it appears in the config.",
        "mark_success_command": f"<python> {daily_script} --config {common['config_path']} mark-success --data-file <DATA_JSON> --digest-file <WEEKLY_MD> --email-status <sent|failed|not-configured>",
        "optional_paper_vault_command": "<python> <paper-vault>/scripts/paper_vault.py import-high --vault-dir <vault-dir> --digest-data-dir <digest-data-dir> --config <config> --priority Medium --max-areas 5 --require-fulltext",
        "safety": [
            "Do not ask for or store mailbox passwords, publisher credentials, raw SMTP secrets, or cookies.",
            "If no selected send-capable route is available, keep the local weekly report and record not-configured or failed; do not silently switch providers.",
            "Paper Vault import is optional and requires full text/local PDF by default; keep title/abstract-only records in the follow-up inbox.",
        ],
    }


def load_config(path: str | Path) -> dict[str, Any]:
    config_path = Path(path)
    try:
        payload = json.loads(config_path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError as exc:
        raise ConfigError(f"configuration file not found: {config_path}") from exc
    except json.JSONDecodeError as exc:
        raise ConfigError(f"invalid JSON in {config_path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ConfigError("configuration root must be a JSON object")
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Plan a unified literature-radar run.")
    sub = parser.add_subparsers(dest="command", required=True)
    plan_parser = sub.add_parser("plan", help="Validate config and print a visualizer or weekly-email plan.")
    plan_parser.add_argument("--mode", choices=MODES, required=True)
    plan_parser.add_argument("--config", required=True)
    plan_parser.add_argument("--output", default="")
    plan_parser.add_argument("--max-per-journal", type=int, default=None)
    # //============XJQ(本次修改：提供独立的执行前依赖检查命令，便于新用户先确认并决定是否安装)====================//
    dependency_parser = sub.add_parser("check-dependencies", help="Probe the dependency matrix before running a mode.")
    dependency_parser.add_argument("--mode", choices=MODES, required=True)
    dependency_parser.add_argument("--skill-root", default="", help="Optional shared skill root to probe.")
    # //============XJQ(本次修改：允许依赖预检明确选择 Gmail、其他邮箱或仅本地报告)====================//
    dependency_parser.add_argument("--delivery-provider", choices=DELIVERY_PROVIDERS, default="gmail")
    # //================XJQ(本次修改：允许依赖预检明确选择 Gmail、其他邮箱或仅本地报告 END===============//
    dependency_parser.add_argument("--output", default="")
    # //================XJQ(本次修改：提供独立的执行前依赖检查命令，便于新用户先确认并决定是否安装 END===============//
    args = parser.parse_args(argv)
    try:
        # //============XJQ(本次修改：允许只检查依赖而不强制读取项目配置)====================//
        if args.command == "check-dependencies":
            dependency_matrix = build_dependency_matrix(args.skill_root or None)
            plan = {
                "mode": args.mode,
                "dependency_matrix": dependency_matrix,
                "delivery_provider": args.delivery_provider,
                "dependency_check": dependency_check(args.mode, dependency_matrix, args.delivery_provider),
                # //============XJQ(本次修改：让无配置文件的依赖预检也能直接提供日报参数询问模板)====================//
                "config_prompt": DEFAULT_CONFIG_PROMPT,
                "reference_defaults": deepcopy(REFERENCE_DEFAULTS),
                # //============XJQ(本次修改：让依赖预检同时显示 Gmail MCP 与其他邮箱的发件选择提示)====================//
                "delivery_prompt": DELIVERY_PROMPT,
                # //================XJQ(本次修改：让依赖预检同时显示 Gmail MCP 与其他邮箱的发件选择提示 END===============//
                # //================XJQ(本次修改：让无配置文件的依赖预检也能直接提供日报参数询问模板 END===============//
            }
        else:
            config = load_config(args.config)
            plan = build_plan(args.mode, config, config_path=args.config, max_per_journal=args.max_per_journal)
        # //================XJQ(本次修改：允许只检查依赖而不强制读取项目配置 END===============//
    except ConfigError as exc:
        parser.error(str(exc))
    rendered = json.dumps(plan, ensure_ascii=False, indent=2)
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered + "\n", encoding="utf-8")
        print(str(output_path.resolve()))
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# //================XJQ(本次修改：实现统一文献雷达的模式路由、配置校验和可执行计划输出 END===============//
