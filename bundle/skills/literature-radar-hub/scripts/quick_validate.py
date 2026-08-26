# //============XJQ(本次修改：提供统一 literature-radar-hub 的无依赖离线校验）====================//
"""Offline validation for the unified literature-radar-hub skill."""

from __future__ import annotations

import re
import sys
from pathlib import Path


def validate(skill_dir: Path) -> list[str]:
    errors: list[str] = []
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return ["SKILL.md is missing"]
    text = skill_md.read_text(encoding="utf-8")
    frontmatter = re.match(r"^---\n(.*?)\n---", text, flags=re.S)
    if not frontmatter:
        errors.append("frontmatter is missing or malformed")
    else:
        header = frontmatter.group(1)
        name = re.search(r"^name:\s*([a-z0-9-]+)\s*$", header, flags=re.M)
        description = re.search(r"^description:\s*(.+)$", header, flags=re.M)
        if not name or name.group(1) != "literature-radar-hub":
            errors.append("frontmatter name must be literature-radar-hub")
        if not description or not description.group(1).strip().startswith("Use when"):
            errors.append("frontmatter description must start with Use when")

    required = [
        skill_dir / "scripts" / "literature_radar_router.py",
        skill_dir / "scripts" / "quick_validate.py",
        skill_dir / "references" / "visualizer-mode.md",
        skill_dir / "references" / "weekly-email-mode.md",
        skill_dir / "agents" / "openai.yaml",
    ]
    errors.extend(f"missing required file: {path.relative_to(skill_dir)}" for path in required if not path.exists())
    for script in sorted((skill_dir / "scripts").glob("*.py")):
        try:
            compile(script.read_text(encoding="utf-8"), str(script), "exec")
        except SyntaxError as exc:
            errors.append(f"syntax error in {script.name}: {exc}")
    # //============XJQ(本次修改：验证依赖预检、矩阵和安装询问规则不会从统一 skill 文档中丢失)====================//
    for marker in (
        "visualizer",
        "weekly-email",
        "max_papers_per_journal",
        "translate_dashboard_zh.py",
        "Dependency preflight",
        "sciencedirect-live-session-fetcher",
        "whether the missing skill may be installed",
        "check-dependencies",
        "Default report configuration prompt",
        "config_prompt",
        "reference_defaults",
        "2026-01-01",
        "Hemodynamics",
    ):
    # //================XJQ(本次修改：验证依赖预检、矩阵和安装询问规则不会从统一 skill 文档中丢失 END===============//
        if marker not in text:
            errors.append(f"SKILL.md is missing marker: {marker}")
    if re.search(r"C:\\Users\\|/Users/|F:\\", text):
        errors.append("SKILL.md contains a machine-specific local path")
    if list(skill_dir.rglob("__pycache__")):
        errors.append("generated __pycache__ folder must not be shipped")
    return errors


def main() -> int:
    skill_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
    errors = validate(skill_dir)
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1
    print("PASS: literature-radar-hub offline validation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# //================XJQ(本次修改：提供统一 literature-radar-hub 的无依赖离线校验 END===============//
