#!/usr/bin/env python3
"""Build an interactive bilingual literature-review dashboard.

The script is deterministic: Codex writes or refines the semantic
dashboard-spec.json after reading metadata/full text, then this script renders
the reusable HTML/JS dashboard. It does not call an LLM and does not fetch
papers.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from pathlib import Path
from typing import Any

from dashboard_common import (
    PALETTE,
    PDF_OPEN_HTML,
    SHARED_CSS,
    SHARED_JS,
    THEME_BOOT_JS,
    inline_js_tag,
    write_js,
    write_json,
)
from large_library_dashboard import write_large_library_dashboard


DETAIL_KEYS = ["topic", "method", "data", "findings", "limits", "relevance"]


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        value = "; ".join(str(item) for item in value if item)
    return re.sub(r"\s+", " ", str(value)).strip()


def read_payload(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8-sig")
    if path.suffix.lower() == ".js":
        _, _, text = text.partition("=")
        text = text.strip().rstrip(";")
    payload = json.loads(text)
    if isinstance(payload, dict):
        return payload
    raise SystemExit(f"Unsupported payload in {path}")


def split_labels(value: Any) -> list[str]:
    text = clean_text(value)
    if not text:
        return []
    parts = re.split(r"\s*[;|,]\s*", text)
    return [part for part in (clean_text(item) for item in parts) if part]


def as_url(value: Any) -> str:
    text = clean_text(value)
    if not text:
        return ""
    if text.startswith("http://") or text.startswith("https://"):
        return text
    if re.match(r"^10\.\S+/\S+$", text):
        return f"https://doi.org/{text}"
    return text


def infer_method(paper: dict[str, Any]) -> str:
    blob = " ".join(
        clean_text(paper.get(key))
        for key in ("methods", "method", "title", "abstract", "topics", "concepts", "keyword_hits")
    ).lower()
    patterns = [
        ("Life Cycle Assessment", r"\b(life cycle assessment|life-cycle assessment|whole-building lca|\blca\b|life cycle carbon)\b"),
        ("Embodied Carbon Accounting", r"\b(embodied carbon|embodied energy|carbon accounting|carbon footprint|material carbon)\b"),
        ("Operational Energy and Retrofit", r"\b(retrofit|renovation|energy efficiency|operational carbon|operational energy|hvac|heat pump)\b"),
        ("Net-Zero / Decarbonization Scenario", r"\b(net zero|zero carbon|carbon neutrality|decarboni[sz]ation|decarboni[sz]e|pathway|scenario)\b"),
        ("Material Circularity and Reuse", r"\b(circular|reuse|recycling|recycled|bio-based|timber|cement|concrete|material)\b"),
        ("Optimization and Decision Support", r"\b(optimization|multi-objective|pareto|decision support|cost-optimal|scenario analysis)\b"),
        ("Policy / Review / Framework", r"\b(policy|barrier|driver|review|framework|roadmap|guideline|taxonomy)\b"),
        ("LLM / Knowledge Graph", r"\b(llm|large language model|gpt|rag|knowledge graph)\b"),
        ("Graph Neural Network", r"\b(graph neural network|gnn|graph learning)\b"),
        ("Reinforcement Learning", r"\b(reinforcement learning|deep reinforcement|rl|drl|marl)\b"),
        ("Physics-Informed AI", r"\b(physics-informed|pinn|neural operator|physical constraint)\b"),
        ("Transformer / Foundation Model", r"\b(transformer|foundation model|vision-language|diffusion)\b"),
        ("Computer Vision", r"\b(computer vision|object detection|segmentation|resnet|yolo|cnn|image)\b"),
        ("ML/DL Prediction and Optimization", r"\b(machine learning|deep learning|xgboost|random forest|neural network|optimization|surrogate)\b"),
    ]
    for label, pattern in patterns:
        if re.search(pattern, blob):
            return label
    labels = split_labels(paper.get("methods"))
    return labels[0] if labels else "Other / Cross-Cutting Method"


def infer_theme(paper: dict[str, Any]) -> str:
    for key in ("theme", "primary_theme", "category"):
        value = clean_text(paper.get(key))
        if value:
            return value
    blob = " ".join(clean_text(paper.get(key)) for key in ("title", "abstract", "topics", "concepts")).lower()
    patterns = [
        ("Whole-Building Carbon Assessment", r"\b(whole-building|life cycle|lca|carbon footprint|carbon accounting)\b"),
        ("Embodied Carbon and Materials", r"\b(embodied carbon|embodied energy|material|concrete|cement|timber|steel|reuse|recycling)\b"),
        ("Net-Zero and Decarbonization Pathways", r"\b(net zero|zero carbon|carbon neutrality|decarboni[sz]ation|pathway|scenario)\b"),
        ("Retrofit and Operational Energy", r"\b(retrofit|renovation|energy efficiency|operational carbon|operational energy|hvac|heat pump)\b"),
        ("Low-Carbon Design and Optimization", r"\b(design|optimization|multi-objective|pareto|cost-optimal|decision support)\b"),
        ("Policy, Adoption, and Barriers", r"\b(policy|barrier|driver|market|adoption|stakeholder|roadmap)\b"),
        ("Digital Tools and Data", r"\b(digital twin|simulation|bim|building information modeling|machine learning|artificial intelligence)\b"),
    ]
    for label, pattern in patterns:
        if re.search(pattern, blob):
            return label
    return "General / Cross-Cutting"


def infer_subtheme(paper: dict[str, Any], theme: str) -> str:
    for key in ("subtheme", "secondary_theme", "topic_cluster"):
        value = clean_text(paper.get(key))
        if value:
            return value
    blob = " ".join(
        clean_text(paper.get(key))
        for key in ("title", "abstract", "methods", "method", "topics", "concepts", "keyword_hits")
    ).lower()
    patterns = [
        ("Energy and HVAC / 能耗与HVAC", r"\b(hvac|thermal comfort|energy consumption|building energy|cooling|heating|demand response)\b"),
        ("Carbon and LCA / 碳排与LCA", r"\b(carbon|emission|life cycle|life-cycle|\blca\b|embodied|decarboni[sz]ation)\b"),
        ("Design Optimization / 设计优化", r"\b(design|optimization|multi-objective|pareto|parametric|performance)\b"),
        ("Simulation and Digital Twin / 仿真与数字孪生", r"\b(simulation|digital twin|bim|building information modeling|energyplus|model(l)?ing)\b"),
        ("AI Prediction / AI预测", r"\b(machine learning|deep learning|neural network|prediction|forecast|data-driven)\b"),
        ("Computer Vision and Sensing / 视觉与感知", r"\b(computer vision|image|object detection|segmentation|sensor|point cloud|remote sensing)\b"),
        ("Materials and Structure / 材料与结构", r"\b(material|concrete|cement|steel|timber|structure|facade|envelope)\b"),
        ("Construction Automation / 建造自动化", r"\b(construction|robot|automation|prefabricat|modular|precast|rebar|site)\b"),
        ("Policy, Review, and Adoption / 政策综述与应用", r"\b(policy|review|framework|barrier|adoption|stakeholder|bibliometric|roadmap)\b"),
        ("Urban and Human Context / 城市与人本环境", r"\b(urban|city|campus|occupant|human|heritage|comfort|behavior)\b"),
    ]
    for label, pattern in patterns:
        if re.search(pattern, blob):
            return label
    if "Review" in theme or "Policy" in theme:
        return "Policy, Review, and Adoption / 政策综述与应用"
    if "Energy" in theme:
        return "Energy and HVAC / 能耗与HVAC"
    if "Materials" in theme:
        return "Materials and Structure / 材料与结构"
    if "AI" in theme:
        return "AI Prediction / AI预测"
    if "Design" in theme:
        return "Design Optimization / 设计优化"
    return "General / 综合交叉"


def normalized_journal(raw: dict[str, Any]) -> str:
    journal = clean_text(raw.get("journal"))
    if journal:
        return journal
    source = clean_text(raw.get("source"))
    if source and source.lower() != "zotero local library":
        return source
    return ""


def cas_partition_of(raw: dict[str, Any]) -> str:
    for key in ("cas_partition", "cas_quartile", "cas", "中科院分区"):
        value = clean_text(raw.get(key))
        match = re.search(r"[1-4]", value)
        if match:
            return match.group(0)
    return ""


def cas_top_of(raw: dict[str, Any]) -> bool:
    for key in ("cas_top", "中科院Top"):
        value = raw.get(key)
        if isinstance(value, bool):
            return value
        text = clean_text(value).lower()
        if text in {"1", "true", "yes", "top", "是"}:
            return True
    return "top" in clean_text(raw.get("cas_partition")).lower()


def int_of(value: Any) -> int:
    try:
        return int(float(clean_text(value) or 0))
    except (TypeError, ValueError):
        return 0


def metadata_quality(raw: dict[str, Any], journal: str, date_value: str, doi: str) -> str:
    missing: list[str] = []
    if not journal:
        missing.append("journal")
    if not date_value:
        missing.append("year/date")
    if not doi:
        missing.append("DOI")
    if missing:
        return "Missing / 缺失: " + ", ".join(missing)
    return "Complete / 完整"


def normalize_papers(raw_papers: list[dict[str, Any]], limit: int | None = None) -> list[dict[str, Any]]:
    papers: list[dict[str, Any]] = []
    for index, raw in enumerate(raw_papers[: limit or len(raw_papers)], start=1):
        if not isinstance(raw, dict):
            continue
        rank = clean_text(raw.get("rank")) or str(index)
        doi = as_url(raw.get("doi_url") or raw.get("doi"))
        journal = normalized_journal(raw)
        date_value = clean_text(raw.get("publication_date") or raw.get("publication_year"))
        theme = clean_text(raw.get("theme") or raw.get("primary_theme") or infer_theme(raw))
        subtheme = clean_text(raw.get("subtheme") or infer_subtheme(raw, theme))
        local_pdf = clean_text(
            raw.get("local_pdf_path")
            or raw.get("local_pdf")
            or raw.get("pdf_path")
            or raw.get("downloaded_pdf")
        )
        papers.append(
            {
                "rank": rank,
                "title": clean_text(raw.get("title")),
                "authors": clean_text(raw.get("authors")),
                "journal": journal,
                "publication_date": date_value,
                "article_type": clean_text(raw.get("article_type")) or "research article",
                "doi": doi,
                "homepage_url": as_url(raw.get("homepage_url")),
                "official_if_evidence_url": as_url(raw.get("official_if_evidence_url") or raw.get("if_evidence_url")),
                "official_impact_factor": clean_text(raw.get("official_impact_factor")),
                "methods": clean_text(raw.get("methods") or raw.get("method") or infer_method(raw)),
                "abstract": clean_text(raw.get("abstract")),
                "access_status": clean_text(raw.get("access_status") or raw.get("full_text_status")),
                "local_pdf_path": local_pdf,
                "theme": theme,
                "subtheme": subtheme,
                "primary_method": clean_text(raw.get("primary_method") or infer_method(raw)),
                "journal_group": clean_text(raw.get("journal_group")) or (journal if journal else "Metadata missing / 元数据缺失"),
                "metadata_quality": clean_text(raw.get("metadata_quality")) or metadata_quality(raw, journal, date_value, doi),
                "cas_partition": cas_partition_of(raw),
                "cas_top": cas_top_of(raw),
                "cited_by_count": int_of(raw.get("cited_by_count")),
                "in_set_cited": int_of(raw.get("in_set_cited")),
                "zotero_item_key": clean_text(raw.get("zotero_item_key")),
            }
        )
    return papers


def paper_delta_key(paper: dict[str, Any]) -> str:
    doi = clean_text(paper.get("doi")).lower()
    doi = re.sub(r"^https?://doi\.org/", "", doi)
    if doi:
        return f"doi:{doi}"
    title = re.sub(r"[^a-z0-9一-鿿]+", "", clean_text(paper.get("title")).lower())
    return f"title:{title[:120]}"


def apply_delta_tracking(papers: list[dict[str, Any]], snapshot_path: Path) -> dict[str, Any]:
    """Mark papers added since the previous build and refresh the snapshot.

    The first build only writes the baseline; nothing is flagged NEW then.
    Returns a summary dict used for the update digest.
    """
    today = dt.date.today().isoformat()
    previous: dict[str, Any] = {}
    if snapshot_path.exists():
        try:
            previous = json.loads(snapshot_path.read_text(encoding="utf-8-sig"))
        except (json.JSONDecodeError, OSError):
            previous = {}
    prev_papers = previous.get("papers") if isinstance(previous.get("papers"), dict) else {}
    had_baseline = bool(prev_papers)
    current_keys: dict[str, dict[str, Any]] = {}
    new_papers: list[dict[str, Any]] = []
    for paper in papers:
        key = paper_delta_key(paper)
        stored = prev_papers.get(key) if isinstance(prev_papers.get(key), dict) else {}
        first_seen = clean_text(stored.get("first_seen")) or today
        is_new = had_baseline and key not in prev_papers
        paper["is_new"] = is_new
        paper["first_seen"] = first_seen
        current_keys[key] = {"first_seen": first_seen, "title": paper.get("title", ""), "rank": paper.get("rank", "")}
        if is_new:
            new_papers.append(paper)
    removed = [
        {"key": key, "title": clean_text((prev_papers.get(key) or {}).get("title"))}
        for key in prev_papers
        if key not in current_keys
    ]
    snapshot = {"last_build": dt.datetime.now().isoformat(timespec="seconds"), "papers": current_keys}
    write_json(snapshot_path, snapshot)
    return {
        "had_baseline": had_baseline,
        "previous_build": clean_text(previous.get("last_build")),
        "new_papers": new_papers,
        "removed": removed,
    }


def if_sort_value(paper: dict[str, Any]) -> float:
    try:
        return float(paper.get("official_impact_factor") or 0)
    except (TypeError, ValueError):
        return 0.0


def write_update_digest(path: Path, delta: dict[str, Any], total: int, title: str) -> bool:
    new_papers = delta.get("new_papers") or []
    removed = delta.get("removed") or []
    if not delta.get("had_baseline") or (not new_papers and not removed):
        return False
    today = dt.date.today().isoformat()
    since = clean_text(delta.get("previous_build"))[:10]
    lines = [
        f"# 文献库更新摘要 / Library Update Digest — {today}",
        "",
        f"- 综述 / Review: {title}",
        f"- 对比基准 / Compared against: {since or 'previous build'}",
        f"- 本次新增 / New papers: **{len(new_papers)}** · 移除 / Removed: {len(removed)} · 当前总数 / Total now: {total}",
        "",
    ]
    if new_papers:
        lines.append("## 新增文献 / New papers")
        lines.append("")
        ordered = sorted(new_papers, key=lambda p: (-if_sort_value(p), str(p.get("publication_date") or "")), reverse=False)
        for index, paper in enumerate(ordered, start=1):
            badges = []
            cas = clean_text(paper.get("cas_partition"))
            if cas:
                badges.append(f"中科院{cas}区" + (" Top" if paper.get("cas_top") else ""))
            if clean_text(paper.get("official_impact_factor")):
                badges.append(f"IF {paper['official_impact_factor']}")
            badge_text = f"（{'，'.join(badges)}）" if badges else ""
            journal = clean_text(paper.get("journal")) or "Journal unknown"
            date_value = clean_text(paper.get("publication_date"))
            doi = clean_text(paper.get("doi"))
            lines.append(f"{index}. **{paper.get('title', '')}** — {journal}{badge_text}")
            detail_bits = [bit for bit in (date_value, doi) if bit]
            if detail_bits:
                lines.append(f"   {' · '.join(detail_bits)}")
        lines.append("")
    if removed:
        lines.append("## 移除 / Removed since last build")
        lines.append("")
        for item in removed:
            lines.append(f"- {item.get('title') or item.get('key')}")
        lines.append("")
    lines.append("---")
    lines.append("Generated by zotero-literature-visualizer · 可直接转发到课题组群 / ready to paste into a group chat.")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return True


def load_citation_network(papers_path: Path) -> dict[str, Any] | None:
    citation_path = papers_path.parent / "citation-network.json"
    if not citation_path.exists():
        return None
    try:
        payload = json.loads(citation_path.read_text(encoding="utf-8-sig"))
    except (json.JSONDecodeError, OSError):
        return None
    edges = payload.get("edges")
    if not isinstance(edges, list):
        return None
    return {
        "generated_at": clean_text(payload.get("generated_at")),
        "edges": [
            {"source": clean_text(edge.get("source")), "target": clean_text(edge.get("target"))}
            for edge in edges
            if isinstance(edge, dict) and clean_text(edge.get("source")) and clean_text(edge.get("target"))
        ],
    }


def make_definitions(labels: list[str], descriptions: dict[str, str] | None = None) -> list[dict[str, str]]:
    descriptions = descriptions or {}
    seen: dict[str, int] = {}
    for label in labels:
        seen[label] = seen.get(label, 0) + 1
    ordered = sorted(seen, key=lambda item: (-seen[item], item.lower()))
    return [
        {
            "name": label,
            "description": descriptions.get(label, "Auto-classified; refine this description after full-text review."),
            "color": PALETTE[index % len(PALETTE)],
        }
        for index, label in enumerate(ordered)
    ]


def bilingual_placeholder(label: str, abstract: str = "") -> dict[str, str]:
    en = abstract[:360] + ("..." if len(abstract) > 360 else "") if abstract else "Add a concise evidence-grounded note after reading the abstract or full text."
    return {
        "zh": f"待补充：围绕“{label}”写出基于证据的中文总结。",
        "en": en,
    }


def init_spec(args: argparse.Namespace) -> None:
    payload = read_payload(Path(args.papers))
    papers = normalize_papers(payload.get("papers", []), args.limit)
    assignments = {
        str(paper["rank"]): {"theme": paper["theme"], "subtheme": paper["subtheme"], "method": paper["primary_method"]}
        for paper in papers
    }
    spec = {
        "title": args.title,
        "subtitle": args.subtitle,
        "layout": "large-library" if len(papers) > 100 else "review-dashboard",
        "theme_definitions": make_definitions([paper["theme"] for paper in papers]),
        "subtheme_definitions": make_definitions([paper["subtheme"] for paper in papers]),
        "method_definitions": make_definitions([paper["primary_method"] for paper in papers]),
        "paper_assignments": assignments,
        "details": {
            str(paper["rank"]): {
                "topic": bilingual_placeholder(assignments[str(paper["rank"])]["theme"], paper["abstract"]),
                "method": bilingual_placeholder(assignments[str(paper["rank"])]["method"]),
                "data": bilingual_placeholder("data/case"),
                "findings": bilingual_placeholder("findings"),
                "limits": bilingual_placeholder("limitations"),
                "relevance": bilingual_placeholder("relevance"),
            }
            for paper in papers
        },
    }
    write_json(Path(args.output), spec)
    print(str(Path(args.output).resolve()))


def load_spec(path: Path, papers: list[dict[str, Any]], title: str, subtitle: str) -> dict[str, Any]:
    if path.exists():
        spec = read_payload(path)
    else:
        spec = {}
    assignments = spec.get("paper_assignments") if isinstance(spec.get("paper_assignments"), dict) else {}
    for paper in papers:
        key = str(paper["rank"])
        row = assignments.get(key) if isinstance(assignments.get(key), dict) else {}
        assignments[key] = {
            "theme": clean_text(row.get("theme")) or paper["theme"],
            "subtheme": clean_text(row.get("subtheme")) or paper["subtheme"],
            "method": clean_text(row.get("method")) or paper["primary_method"],
        }
    theme_defs = spec.get("theme_definitions") if isinstance(spec.get("theme_definitions"), list) else []
    subtheme_defs = spec.get("subtheme_definitions") if isinstance(spec.get("subtheme_definitions"), list) else []
    method_defs = spec.get("method_definitions") if isinstance(spec.get("method_definitions"), list) else []
    if not theme_defs:
        theme_defs = make_definitions([assignments[str(p["rank"])]["theme"] for p in papers])
    if not subtheme_defs:
        subtheme_defs = make_definitions([assignments[str(p["rank"])]["subtheme"] for p in papers])
    if not method_defs:
        method_defs = make_definitions([assignments[str(p["rank"])]["method"] for p in papers])
    details: dict[str, Any] = {}
    if isinstance(spec.get("paper_details"), dict):
        details.update(spec["paper_details"])
    if isinstance(spec.get("details"), dict):
        details.update(spec["details"])
    return {
        "title": clean_text(spec.get("title")) or title,
        "subtitle": clean_text(spec.get("subtitle")) or subtitle,
        "layout": clean_text(spec.get("layout")) or ("large-library" if len(papers) > 100 else "review-dashboard"),
        "theme_definitions": theme_defs,
        "subtheme_definitions": subtheme_defs,
        "method_definitions": method_defs,
        "paper_assignments": assignments,
        "details": details,
    }


DASHBOARD_HTML = r"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Literature Review Dashboard</title>
  <script>__THEME_BOOT__</script>
  <style>
__SHARED_CSS__
    main { width:min(1200px, calc(100vw - 36px)); margin:0 auto; padding:26px 0 48px; }
    h1 { font-size:31px; line-height:1.18; }
    h2 { font-size:19px; line-height:1.3; }
    .hero { display:grid; grid-template-columns:1.3fr .7fr; gap:14px; align-items:stretch; margin-bottom:14px; }
    .intro { padding:20px 22px; display:flex; flex-direction:column; }
    .intro .brandline { margin-bottom:15px; }
    .intro-top { display:flex; justify-content:space-between; gap:12px; align-items:flex-start; }
    .intro-heading h1 { margin-top:7px; }
    .subtitle { color:var(--muted); font-size:13px; line-height:1.55; margin-top:9px; }
    .intro .searchbar { margin-top:auto; padding-top:15px; }
    .kpis { grid-template-columns:repeat(2,minmax(0,1fr)); }
    .layout { display:grid; grid-template-columns:1fr 1fr; gap:14px; align-items:start; }
    .panel { padding:18px 20px; overflow:hidden; }
    .panel-head { margin-bottom:12px; }
    .panel-head .hint { margin-top:5px; }
    .section { margin-top:14px; }
    .viz { display:grid; grid-template-columns:230px minmax(0,1fr); gap:18px; align-items:center; }
    .donut-wrap { position:relative; width:210px; height:210px; margin:0 auto; }
    .donut { width:210px; height:210px; display:block; }
    .donut-track { fill:none; stroke:var(--track); stroke-width:22; }
    .segment { fill:none; stroke-width:22; cursor:pointer;
      transition:stroke-dasharray .55s cubic-bezier(.25,.7,.3,1), stroke-dashoffset .55s cubic-bezier(.25,.7,.3,1), opacity .18s ease, stroke-width .18s ease; }
    .segment.dim { opacity:.25; }
    .segment.active { stroke-width:27; }
    .donut-center { position:absolute; inset:56px; display:grid; place-content:center; text-align:center; border-radius:999px; background:var(--panel); border:1px solid var(--line); }
    .donut-center strong { font-size:31px; line-height:1; font-variant-numeric:tabular-nums; font-family:var(--font-display); font-weight:640; }
    .donut-center span { color:var(--muted); font-size:11px; margin-top:5px; }
    .legend { display:grid; gap:7px; }
    .chip { display:grid; grid-template-columns:11px 1fr auto; gap:9px; align-items:center; width:100%; text-align:left; min-height:40px; padding:8px 11px; }
    .chip i { width:11px; height:11px; border-radius:999px; display:block; }
    .chip span { min-width:0; font-size:12px; line-height:1.3; }
    .chip strong { color:var(--muted); font-size:12px; font-variant-numeric:tabular-nums; }
    .chip[aria-pressed="true"] strong { color:inherit; }
    .relation-wrap { overflow-x:auto; }
    .relation-svg { width:100%; min-width:760px; display:block; }
    .ribbon { fill:none; cursor:pointer; transition:opacity .18s ease; }
    .relation-label { font-size:12.5px; font-weight:650; cursor:pointer; fill:var(--ink); }
    .relation-label:hover { text-decoration:underline; }
    .relation-label tspan.cnt { fill:var(--muted); font-weight:500; font-size:11.5px; }
    .relation-label tspan.l2 { fill:var(--muted); font-weight:500; font-size:11px; }
    .node-dot { cursor:pointer; }
    .cite-wrap { display:grid; grid-template-columns:minmax(0,1fr) 280px; gap:16px; align-items:start; }
    .cite-svg { width:100%; min-width:700px; display:block; }
    .cite-arc { fill:none; stroke-width:1.7; opacity:.4; cursor:pointer; transition:opacity .15s ease, stroke-width .15s ease; }
    .cite-arc.hl { opacity:.95; stroke-width:2.8; }
    .cite-arc.dimmed { opacity:.05; }
    .cite-node { cursor:pointer; stroke:var(--panel); stroke-width:1.5; transition:opacity .15s ease; }
    .cite-node.core { stroke:var(--accent); stroke-width:2.5; }
    .cite-node.dimmed { opacity:.2; }
    .cite-rank { font-size:9.5px; fill:var(--muted); text-anchor:middle; pointer-events:none; font-variant-numeric:tabular-nums; }
    .cite-core h3 { font-size:14.5px; margin-bottom:9px; }
    .core-item { display:grid; grid-template-columns:auto minmax(0,1fr); gap:9px; align-items:start; border:1px solid var(--line); border-radius:9px; padding:8px 10px; margin-bottom:8px; cursor:pointer; background:var(--panel); }
    .core-item:hover { border-color:var(--line-strong); background:var(--panel-2); }
    .core-item .cnum { font-family:var(--font-display); font-weight:700; font-size:19px; color:var(--accent); line-height:1.1; min-width:22px; text-align:center; }
    .core-item .cnum span { display:block; font-family:inherit; font-size:9px; color:var(--muted); font-weight:500; }
    .core-item strong { font-size:12px; line-height:1.35; font-weight:640; display:block; }
    .core-item em { color:var(--muted); font-size:11px; display:block; margin-top:2px; font-style:normal; }
    .relation-label-sub { font-size:10.5px; fill:var(--muted); letter-spacing:.1em; font-weight:650; }
    .cards { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:12px; }
    .card { padding:14px 16px 13px; border-radius:12px; box-shadow:none; cursor:pointer; border-left:3px solid var(--pc, var(--line));
      transition:border-color .16s ease, transform .16s ease, box-shadow .16s ease; }
    .card:hover { border-color:var(--line-strong); border-left-color:var(--pc, var(--line-strong)); transform:translateY(-2px); box-shadow:var(--shadow); }
    .card-eyebrow { display:flex; gap:8px; align-items:center; color:var(--muted); font-size:11.5px; min-width:0; }
    .card-eyebrow .rankno { font-variant-numeric:tabular-nums; font-weight:650; opacity:.7; flex-shrink:0; }
    .card-eyebrow .je { font-weight:650; color:var(--ink); opacity:.8; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; min-width:0; }
    .card-eyebrow .dt { white-space:nowrap; font-variant-numeric:tabular-nums; flex-shrink:0; }
    .card-eyebrow .tag { flex-shrink:0; }
    .sp { flex:1; }
    .card h3 { font-family:var(--font-display); font-size:15.5px; line-height:1.42; margin-top:8px; font-weight:640; }
    .card-authors { color:var(--muted); font-size:12px; margin-top:6px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
    .card-abstract { color:var(--muted); font-size:12.5px; line-height:1.55; margin-top:6px; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden; }
    .card-foot { display:flex; gap:6px; align-items:center; margin-top:11px; flex-wrap:wrap; }
    .results-head { display:flex; justify-content:space-between; align-items:center; gap:10px; flex-wrap:wrap; margin-bottom:12px; }
    .results-actions { display:flex; gap:8px; align-items:center; flex-wrap:wrap; }
    .results-actions select { width:auto; min-height:34px; padding:6px 9px; }
    .result-count { color:var(--muted); font-size:12px; }
    .empty { color:var(--muted); padding:26px; text-align:center; border:1px dashed var(--line); border-radius:12px; grid-column:1/-1; }
    @media (max-width:980px) {
      main { width:min(100vw - 24px, 760px); padding-top:18px; }
      .hero, .layout, .cards { grid-template-columns:minmax(0,1fr); }
      .viz { grid-template-columns:minmax(0,1fr); }
      .cite-wrap { grid-template-columns:minmax(0,1fr); }
      .detail-grid { grid-template-columns:minmax(0,1fr); }
      .bar { grid-template-columns:minmax(0,1fr); }
      .card { min-width:0; }
      .card-eyebrow { flex-wrap:wrap; }
      .count { text-align:left; }
    }
  </style>
</head>
<body>
<main>
  <section class="hero">
    <div class="intro panel">
      <div class="brandline"></div>
      <div class="intro-top">
        <div class="intro-heading">
          <div class="eyebrow-label"><span class="lz">文献综述</span><span class="sep"> · </span><span class="le">Literature Review</span></div>
          <h1 id="dashTitle"></h1>
          <p class="subtitle" id="dashSubtitle"></p>
        </div>
        <div class="toolbar">
          <button class="ghost" type="button" id="shareCard" title="导出分享卡海报 / Export share-card poster">分享卡</button>
          <button class="ghost" type="button" id="langToggle">双语</button>
          <button class="ghost" type="button" id="themeToggle">◐</button>
        </div>
      </div>
      <div class="searchbar">
        <input type="search" id="searchInput" autocomplete="off"
          placeholder="搜索标题、作者、期刊、摘要… / Search title, authors, journal, abstract…">
        <span class="slash-hint">/</span>
      </div>
      <div class="readbar" id="readbar"></div>
    </div>
    <div class="kpis">
      <div class="kpi" id="kpiPapers" role="button" tabindex="0" title="清除全部筛选 / Clear all filters">
        <div class="label">Papers</div><div class="value" id="paperCount">0</div>
        <div class="note"><span class="lz">纳入文献（点击清除筛选）</span><span class="sep"> · </span><span class="le">included records (click to reset)</span></div>
      </div>
      <div class="kpi"><div class="label">Themes</div><div class="value" id="themeKpi">0</div>
        <div class="note"><span class="lz">主题分类数</span><span class="sep"> · </span><span class="le">topic categories</span></div></div>
      <div class="kpi"><div class="label">Methods</div><div class="value" id="methodKpi">0</div>
        <div class="note"><span class="lz">方法族数</span><span class="sep"> · </span><span class="le">method families</span></div></div>
      <div class="kpi" id="kpiPdf" role="button" tabindex="0" title="查看缺少 PDF 的文献 / Show papers missing a local PDF">
        <div class="label">PDFs</div><div class="value" id="pdfKpi">0</div>
        <div class="note"><span class="lz">本地 PDF（点击筛选缺失）</span><span class="sep"> · </span><span class="le">local files (click for missing)</span></div>
      </div>
    </div>
  </section>

  <div class="chipbar" id="chipBar" hidden></div>

  <section class="layout">
    <article class="panel">
      <div class="panel-head">
        <h2><span class="lz">主题分类</span><span class="sep"> / </span><span class="le">Theme Taxonomy</span></h2>
        <p class="hint"><span class="lz">点击扇区或图例联动筛选全部视图，再点一次取消。</span><span class="sep"> </span><span class="le">Click a slice or legend chip to filter every view; click again to clear.</span></p>
      </div>
      <div class="viz">
        <div class="donut-wrap">
          <svg class="donut" id="themeDonut" viewBox="0 0 180 180"></svg>
          <div class="donut-center"><strong id="themeCount">0</strong><span><span class="lz">篇</span><span class="sep"> </span><span class="le">papers</span></span></div>
        </div>
        <div class="legend" id="themeLegend"></div>
      </div>
    </article>
    <article class="panel">
      <div class="panel-head">
        <h2><span class="lz">方法热度</span><span class="sep"> / </span><span class="le">Method Hotspots</span></h2>
        <p class="hint"><span class="lz">与主题筛选联动：在当前子集内统计方法分布。</span><span class="sep"> </span><span class="le">Faceted with the theme filter: method counts follow the current subset.</span></p>
      </div>
      <div class="viz">
        <div class="donut-wrap">
          <svg class="donut" id="methodDonut" viewBox="0 0 180 180"></svg>
          <div class="donut-center"><strong id="methodCount">0</strong><span><span class="lz">篇</span><span class="sep"> </span><span class="le">papers</span></span></div>
        </div>
        <div class="legend" id="methodLegend"></div>
      </div>
    </article>
  </section>

  <section class="panel section" id="timelinePanel" hidden>
    <div class="panel-head">
      <h2><span class="lz">发表时间线</span><span class="sep"> / </span><span class="le">Publication Timeline</span></h2>
      <p class="hint"><span class="lz">按月份统计，点击月份筛选。</span><span class="sep"> </span><span class="le">Monthly counts; click a month to filter.</span></p>
    </div>
    <div class="tl" id="timeline"></div>
  </section>

  <section class="panel section">
    <div class="panel-head">
      <h2><span class="lz">主题 × 方法关系流图</span><span class="sep"> / </span><span class="le">Theme-Method Flow Map</span></h2>
      <p class="hint"><span class="lz">丝带宽度代表该主题-方法组合的文章数；点击丝带筛选该组合，点击左右标签单独筛选。</span><span class="sep"> </span><span class="le">Ribbon width = papers in that theme-method pair. Click a ribbon to filter the pair; click side labels to filter one dimension.</span></p>
    </div>
    <div class="relation-wrap"><svg class="relation-svg" id="relationSvg" viewBox="0 0 980 400"></svg></div>
  </section>

  <section class="panel section" id="citePanel" hidden>
    <div class="panel-head">
      <h2><span class="lz">引用关系网络</span><span class="sep"> / </span><span class="le">Citation Network</span></h2>
      <p class="hint"><span class="lz">弧线 = 集合内引用（引用方 → 被引方）；节点大小 = 在本集合内被引次数，外圈高亮为核心必读。悬停看关系，点击节点看详情。</span><span class="sep"> </span><span class="le">Arcs are in-set citations (citing → cited); node size = times cited within this collection, ringed nodes are core must-reads. Hover to trace, click a node for details.</span></p>
    </div>
    <div class="cite-wrap">
      <div class="relation-wrap"><svg class="cite-svg" id="citeSvg"></svg></div>
      <aside class="cite-core">
        <h3 id="citeCoreTitle"></h3>
        <div id="citeCore"></div>
      </aside>
    </div>
  </section>

  <section class="panel section">
    <div class="panel-head">
      <h2><span class="lz">期刊来源</span><span class="sep"> / </span><span class="le">Journal Sources</span></h2>
      <p class="hint"><span class="lz">条长代表当前筛选下的文章数；IF 徽标显示官方影响因子。点击期刊行筛选。</span><span class="sep"> </span><span class="le">Bar length = paper count in the current view; the IF badge shows the verified impact factor. Click a row to filter.</span></p>
    </div>
    <div class="bars" id="journalBars"></div>
  </section>

  <section class="panel section">
    <div class="results-head">
      <div>
        <h2><span class="lz">文章卡片</span><span class="sep"> / </span><span class="le">Paper Cards</span></h2>
        <p class="hint result-count" id="cardCount"></p>
      </div>
      <div class="results-actions">
        <select id="readSelect" title="按阅读状态筛选 / Filter by reading status">
          <option value="">状态：全部 All</option>
          <option value="fresh">NEW 本次新增</option>
          <option value="unread">未读 Unread</option>
          <option value="reading">在读 Reading</option>
          <option value="read">已读 Read</option>
          <option value="starred">★ 星标 Starred</option>
        </select>
        <select id="sortSelect" title="排序 / Sort">
          <option value="rank">排序：Rank</option>
          <option value="year">排序：最新 Newest</option>
          <option value="if">排序：IF</option>
          <option value="cited">排序：被引 Cited</option>
        </select>
        <button type="button" id="exportCsv" title="导出当前筛选（含我的笔记）/ Export current view incl. notes">CSV</button>
        <button type="button" id="exportBib" title="导出当前筛选 / Export current view">BibTeX</button>
        <button type="button" id="exportZotero" title="导出 Zotero 回写包：分类/阅读状态/笔记，配合 zotero_api_import.py write-back 同步回 Zotero / Export write-back package for Zotero sync">Zotero</button>
      </div>
    </div>
    <div class="cards" id="cards"></div>
  </section>
</main>

<aside class="detail-shell" id="detailShell" aria-hidden="true">
  <article class="detail-card" role="dialog" aria-modal="true" id="detailCard">
    <div class="detail-top">
      <div><div class="eyebrow" id="detailEyebrow"></div><h2 id="detailTitle"></h2></div>
      <div class="detail-actions">
        <button class="icon-button" type="button" id="detailPrev" title="上一篇 (←) / Previous">‹</button>
        <button class="icon-button" type="button" id="detailNext" title="下一篇 (→) / Next">›</button>
        <button class="icon-button" type="button" id="detailClose" title="关闭 (Esc) / Close">×</button>
      </div>
    </div>
    <div class="tags" id="detailTags"></div>
    <div class="detail-grid" id="detailFacts"></div>
    <div id="detailSections"></div>
    <div id="detailNotes"></div>
    <div class="detail-links" id="detailLinks"></div>
  </article>
</aside>

__DATA_SCRIPT__
__DETAILS_SCRIPT__
<script>
__SHARED_JS__
</script>
<script>
  const S = window.SLR;
  const data = window.__SLR_DASHBOARD_DATA__ || { papers: [], spec: {} };
  const papers = data.papers || [];
  const spec = data.spec || {};
  const details = window.__SLR_DASHBOARD_DETAILS__ || {};
  const themeDefs = spec.theme_definitions || [];
  const methodDefs = spec.method_definitions || [];
  const assignments = spec.paper_assignments || {};
  const R = 67, C = 2 * Math.PI * R;
  const esc = S.escapeHtml, B = S.B;
  const notes = S.initNotes(`slr-notes:${spec.title || "dashboard"}|${papers.length}`);

  const state = { q: "", theme: null, method: null, journal: null, month: null, pdf: null, read: null, sort: "rank" };
  let activeRank = null;
  let releaseFocus = null;
  let navList = papers;
  let booted = false;

  function paperTheme(p) { return (assignments[String(p.rank)] || {}).theme || p.theme || "Unclassified"; }
  function paperMethod(p) { return (assignments[String(p.rank)] || {}).method || p.primary_method || p.methods || "Other"; }
  function paperSubtheme(p) { return (assignments[String(p.rank)] || {}).subtheme || p.subtheme || ""; }
  function paperJournal(p) { return p.journal || "Unknown"; }
  function rankNum(p) { const n = Number(p.rank); return Number.isFinite(n) ? n : 0; }
  function colorFor(defs, name) { const d = defs.find(x => x.name === name); return S.resolveColor((d && d.color) || "#7b8a97"); }
  function localPageUrl(page) { return new URL(page, location.href.split("#")[0]).href; }
  function pdfLauncherUrl(paper) { return localPageUrl(`__PDF_OPEN_FILE__?rank=${encodeURIComponent(paper.rank)}`); }

  function passes(p, skip) {
    if (skip !== "q" && state.q && !S.matchesQuery(p, state.q)) return false;
    if (skip !== "theme" && state.theme && paperTheme(p) !== state.theme) return false;
    if (skip !== "method" && state.method && paperMethod(p) !== state.method) return false;
    if (skip !== "journal" && state.journal && paperJournal(p) !== state.journal) return false;
    if (skip !== "month" && state.month && S.monthOf(p) !== state.month) return false;
    if (skip !== "pdf" && state.pdf === "missing" && p.local_pdf_path) return false;
    if (skip !== "read" && state.read) {
      if (state.read === "fresh") { if (!p.is_new) return false; }
      else if (!notes.matches(p.rank, state.read)) return false;
    }
    return true;
  }
  function sortPapers(list) {
    const l = list.slice();
    if (state.sort === "year") {
      l.sort((a, b) => String(b.publication_date || "").localeCompare(String(a.publication_date || "")) || rankNum(a) - rankNum(b));
    } else if (state.sort === "if") {
      l.sort((a, b) => (Number(b.official_impact_factor) || 0) - (Number(a.official_impact_factor) || 0) || rankNum(a) - rankNum(b));
    } else if (state.sort === "cited") {
      l.sort((a, b) => (b.in_set_cited || 0) - (a.in_set_cited || 0) || (b.cited_by_count || 0) - (a.cited_by_count || 0) || rankNum(a) - rankNum(b));
    } else {
      l.sort((a, b) => rankNum(a) - rankNum(b));
    }
    return l;
  }
  function visiblePapers() { return sortPapers(papers.filter(p => passes(p, null))); }
  function facetCounts(keyFn, skip) {
    const map = new Map();
    papers.forEach(p => { if (passes(p, skip)) { const k = keyFn(p); map.set(k, (map.get(k) || 0) + 1); } });
    return map;
  }
  function clearFilters() {
    state.q = ""; state.theme = null; state.method = null; state.journal = null; state.month = null; state.pdf = null; state.read = null;
    document.getElementById("searchInput").value = "";
    document.getElementById("readSelect").value = "";
    renderAll();
  }

  function ensureDonut(svgId, defs, kind) {
    const svg = document.getElementById(svgId);
    if (svg.dataset.built) return;
    svg.innerHTML = `<circle class="donut-track" cx="90" cy="90" r="${R}"></circle>` + defs.map(def =>
      `<circle class="segment" tabindex="0" role="button" cx="90" cy="90" r="${R}"
        style="stroke:${S.resolveColor(def.color)};stroke-dasharray:0 ${C};stroke-dashoffset:0" transform="rotate(-90 90 90)"
        aria-label="${esc(def.name)}"></circle>`).join("");
    const segs = svg.querySelectorAll(".segment");
    defs.forEach((def, i) => {
      const el = segs[i];
      const toggle = () => { state[kind] = state[kind] === def.name ? null : def.name; renderAll(); };
      el.addEventListener("click", toggle);
      el.addEventListener("keydown", e => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); toggle(); } });
      S.bindTip(el, () => `<b>${esc(def.name)}</b><br>${esc(el.dataset.n || 0)} · ${esc(el.dataset.pct || "0%")}`);
    });
    svg.dataset.built = "1";
  }
  function updateDonut(svgId, defs, counts, active) {
    const svg = document.getElementById(svgId);
    const segs = svg.querySelectorAll(".segment");
    const total = [...counts.values()].reduce((a, b) => a + b, 0);
    const nonzero = defs.filter(def => (counts.get(def.name) || 0) > 0).length;
    const gap = nonzero > 1 ? 2.4 : 0;
    let offset = 0;
    defs.forEach((def, i) => {
      const el = segs[i];
      const n = counts.get(def.name) || 0;
      const len = total ? n / total * C : 0;
      const seg = Math.max(len - gap, len > 0 ? 0.5 : 0);
      el.style.strokeDasharray = `${seg} ${C - seg}`;
      el.style.strokeDashoffset = String(-(offset + gap / 2));
      offset += len;
      el.dataset.n = String(n);
      el.dataset.pct = total ? Math.round(n / total * 100) + "%" : "0%";
      el.classList.toggle("active", active === def.name);
      el.classList.toggle("dim", !!active && active !== def.name);
    });
    return total;
  }
  function renderLegend(targetId, defs, counts, active, kind) {
    const box = document.getElementById(targetId);
    box.innerHTML = defs.map(def => {
      const n = counts.get(def.name) || 0;
      return `<button class="chip" type="button" data-name="${esc(def.name)}" aria-pressed="${active === def.name}">
        <i style="background:${S.resolveColor(def.color)}"></i><span>${esc(def.name)}</span><strong>${n}</strong></button>`;
    }).join("");
    box.querySelectorAll(".chip").forEach(btn => btn.addEventListener("click", () => {
      state[kind] = state[kind] === btn.dataset.name ? null : btn.dataset.name;
      renderAll();
    }));
  }
  function renderCategory(kind) {
    const isTheme = kind === "theme";
    const defs = isTheme ? themeDefs : methodDefs;
    const counts = facetCounts(isTheme ? paperTheme : paperMethod, kind);
    const active = state[kind];
    ensureDonut(`${kind}Donut`, defs, kind);
    const total = updateDonut(`${kind}Donut`, defs, counts, active);
    renderLegend(`${kind}Legend`, defs, counts, active, kind);
    document.getElementById(`${kind}Count`).textContent = active ? (counts.get(active) || 0) : total;
  }

  function shortLabel(name, max) { const t = String(name); return t.length > max ? t.slice(0, max - 1) + "…" : t; }
  function pairKey(theme, method) { return theme + "|||" + method; }
  function renderRelation() {
    const svg = document.getElementById("relationSvg");
    const totals = new Map();
    papers.forEach(p => {
      const k = pairKey(paperTheme(p), paperMethod(p));
      if (!totals.has(k)) totals.set(k, { theme: paperTheme(p), method: paperMethod(p), all: [], cur: 0 });
      totals.get(k).all.push(p);
    });
    papers.forEach(p => { if (passes(p, null)) totals.get(pairKey(paperTheme(p), paperMethod(p))).cur += 1; });
    const pairs = [...totals.values()].sort((a, b) => b.all.length - a.all.length);
    const themes = themeDefs.map(d => d.name).filter(name => papers.some(p => paperTheme(p) === name));
    const methods = methodDefs.map(d => d.name).filter(name => papers.some(p => paperMethod(p) === name));
    const rows = Math.max(themes.length, methods.length);
    const top = 44, rowGap = Math.max(46, Math.min(64, 340 / Math.max(rows - 1, 1)));
    const bottom = top + (rows - 1) * rowGap;
    const H = bottom + 40;
    svg.setAttribute("viewBox", `0 0 980 ${H}`);
    const leftX = 250, rightX = 726;
    const centerFor = (n, i) => top + ((rows - n) * rowGap) / 2 + i * rowGap;
    const themeY = new Map(themes.map((name, i) => [name, centerFor(themes.length, i)]));
    const methodY = new Map(methods.map((name, i) => [name, centerFor(methods.length, i)]));
    const maxN = Math.max(...pairs.map(p => p.all.length), 1);
    const themeCounts = facetCounts(paperTheme, null);
    const methodCounts = facetCounts(paperMethod, null);
    const ribbons = pairs.map(pair => {
      const y1 = themeY.get(pair.theme) || top;
      const y2 = methodY.get(pair.method) || top;
      const d = `M ${leftX} ${y1} C ${leftX + 170} ${y1}, ${rightX - 170} ${y2}, ${rightX} ${y2}`;
      const width = 3 + Math.round(pair.all.length / maxN * 15);
      const activePair = state.theme === pair.theme && state.method === pair.method;
      const opacity = pair.cur > 0 ? (activePair ? .95 : .58) : .07;
      return `<path class="ribbon" d="${d}" stroke="${colorFor(themeDefs, pair.theme)}" stroke-width="${width}"
        style="opacity:${opacity}" data-theme="${esc(pair.theme)}" data-method="${esc(pair.method)}"></path>`;
    }).join("");
    const label = (name, x, y, anchor, color, kind, count) => {
      const parts = String(name).split(/\s+\/\s+/);
      const second = parts.slice(1).join(" / ");
      const line2 = second ? `<tspan class="l2" x="${x}" dy="13.5">${esc(shortLabel(second, 26))}</tspan>` : "";
      return `<text class="relation-label" x="${x}" y="${y + (second ? -2 : 4)}" text-anchor="${anchor}" data-kind="${kind}" data-name="${esc(name)}">
        ${esc(shortLabel(parts[0], 30))} <tspan class="cnt">${count}</tspan>${line2}<title>${esc(name)}</title></text>
       <circle class="node-dot" cx="${anchor === "end" ? x + 12 : x - 12}" cy="${y}" r="4.5" fill="${color}" data-kind="${kind}" data-name="${esc(name)}"></circle>`;
    };
    const leftLabels = themes.map(name =>
      label(name, leftX - 22, themeY.get(name), "end", colorFor(themeDefs, name), "theme", themeCounts.get(name) || 0)).join("");
    const rightLabels = methods.map(name =>
      label(name, rightX + 22, methodY.get(name), "start", colorFor(methodDefs, name), "method", methodCounts.get(name) || 0)).join("");
    svg.innerHTML = `<text class="relation-label-sub" x="20" y="18">主题 THEME</text>
      <text class="relation-label-sub" x="${rightX + 22}" y="18">方法 METHOD</text>${ribbons}${leftLabels}${rightLabels}`;
    svg.querySelectorAll(".ribbon").forEach(path => {
      const t = path.dataset.theme, m = path.dataset.method;
      path.addEventListener("click", () => {
        if (state.theme === t && state.method === m) { state.theme = null; state.method = null; }
        else { state.theme = t; state.method = m; }
        renderAll();
      });
      S.bindTip(path, () => {
        const pair = totals.get(pairKey(t, m));
        const items = pair.all.slice(0, 2).map(p => `<span class="tip-sub">· ${esc(shortLabel(p.title, 46))}</span>`).join("");
        const more = pair.all.length > 2 ? `<span class="tip-sub">… ${B("等", "and")} ${pair.all.length - 2} ${B("篇", "more")}</span>` : "";
        return `<b>${esc(t)}</b> × <b>${esc(m)}</b> · ${pair.all.length}${items}${more}`;
      });
    });
    svg.querySelectorAll(".relation-label, .node-dot").forEach(labelEl => {
      labelEl.addEventListener("click", () => {
        const kind = labelEl.dataset.kind;
        state[kind] = state[kind] === labelEl.dataset.name ? null : labelEl.dataset.name;
        renderAll();
      });
    });
  }

  let timelineKeys = [];
  function buildTimeline() {
    timelineKeys = [...new Set(papers.map(S.monthOf).filter(Boolean))].sort();
    document.getElementById("timelinePanel").hidden = timelineKeys.length < 2;
  }
  function renderTimeline() {
    if (document.getElementById("timelinePanel").hidden) return;
    const counts = facetCounts(S.monthOf, "month");
    const max = Math.max(...timelineKeys.map(k => counts.get(k) || 0), 1);
    const box = document.getElementById("timeline");
    box.innerHTML = timelineKeys.map(key => {
      const n = counts.get(key) || 0;
      const h = Math.round(n / max * 100);
      const label = key.slice(2).replace("-", ".");
      return `<button class="tl-col" type="button" data-month="${esc(key)}" data-n="${n}" aria-pressed="${state.month === key}">
        <span class="tl-bar"><span class="tl-fill" style="height:${Math.max(h, n ? 6 : 0)}%"></span></span>
        <span class="tl-n">${n || ""}</span><span class="tl-lab">${esc(label)}</span></button>`;
    }).join("");
    box.querySelectorAll(".tl-col").forEach(btn => {
      btn.addEventListener("click", () => { state.month = state.month === btn.dataset.month ? null : btn.dataset.month; renderAll(); });
      S.bindTip(btn, () => `<b>${esc(btn.dataset.month)}</b><br>${esc(btn.dataset.n)}`);
    });
  }

  function renderJournals() {
    const counts = facetCounts(paperJournal, "journal");
    const rows = [];
    counts.forEach((n, name) => {
      const items = papers.filter(p => paperJournal(p) === name);
      const ifValue = Math.max(...items.map(p => Number(p.official_impact_factor) || 0), 0);
      const hit = items.find(p => p.homepage_url || p.official_if_evidence_url) || {};
      const casHit = items.find(p => S.casTier(p));
      rows.push({ name, n, ifValue, url: hit.homepage_url || hit.official_if_evidence_url || "", casHtml: casHit ? S.casTagHtml(casHit) : "" });
    });
    rows.sort((a, b) => b.n - a.n || b.ifValue - a.ifValue || a.name.localeCompare(b.name));
    const max = Math.max(...rows.map(r => r.n), 1);
    document.getElementById("journalBars").innerHTML = rows.map(r => {
      const ifBadge = r.ifValue ? ` <span class="tag if">IF ${r.ifValue.toFixed(1)}</span>` : "";
      const link = r.url ? `<a href="${esc(r.url)}" target="_blank" rel="noopener">${B("期刊官网", "Journal homepage")} ↗</a>` : `<span>${B("官网待核", "homepage unverified")}</span>`;
      return `<div class="bar" role="button" tabindex="0" data-journal="${esc(r.name)}" aria-pressed="${state.journal === r.name}">
        <div class="bar-name">${esc(r.name)}${r.casHtml ? " " + r.casHtml : ""}${ifBadge}<span class="sub">${link}</span></div>
        <div class="track"><div class="fill" style="width:${Math.max(6, Math.round(r.n / max * 100))}%"></div></div>
        <div class="count">${r.n}</div></div>`;
    }).join("");
    document.querySelectorAll("#journalBars .bar").forEach(bar => {
      const toggle = () => { state.journal = state.journal === bar.dataset.journal ? null : bar.dataset.journal; renderAll(); };
      bar.addEventListener("click", e => { if (e.target.closest("a")) return; toggle(); });
      bar.addEventListener("keydown", e => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); toggle(); } });
    });
  }

  const citations = data.citations || null;
  const citeEdges = ((citations && citations.edges) || []).filter(e =>
    papers.some(p => String(p.rank) === String(e.source)) && papers.some(p => String(p.rank) === String(e.target)));
  const inSetMap = (function () {
    const m = new Map();
    citeEdges.forEach(e => m.set(String(e.target), (m.get(String(e.target)) || 0) + 1));
    papers.forEach(p => {
      const k = String(p.rank);
      m.set(k, Math.max(m.get(k) || 0, p.in_set_cited || 0));
    });
    return m;
  })();
  function inSetCited(p) { return inSetMap.get(String(p.rank)) || 0; }
  function hasCiteData() { return citeEdges.length > 0 || papers.some(p => (p.cited_by_count || 0) > 0 || inSetCited(p) > 0); }
  function coreRanks() {
    const ranked = papers.filter(p => inSetCited(p) > 0)
      .sort((a, b) => inSetCited(b) - inSetCited(a) || (b.cited_by_count || 0) - (a.cited_by_count || 0));
    return new Set(ranked.slice(0, 5).map(p => String(p.rank)));
  }
  function renderCitations() {
    const panel = document.getElementById("citePanel");
    if (!hasCiteData()) { panel.hidden = true; return; }
    panel.hidden = false;
    const svg = document.getElementById("citeSvg");
    const ordered = papers.slice().sort((a, b) => rankNum(a) - rankNum(b));
    const n = ordered.length;
    const W = 960, left = 34, right = W - 34;
    const span = right - left;
    const maxIn = Math.max(...ordered.map(inSetCited), 1);
    const H = 236, baseY = H - 42;
    svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
    const xOf = new Map(ordered.map((p, i) => [String(p.rank), n > 1 ? left + i * span / (n - 1) : W / 2]));
    const core = coreRanks();
    const arcs = citeEdges.map(e => {
      const x1 = xOf.get(String(e.source)), x2 = xOf.get(String(e.target));
      const src = papers.find(p => String(p.rank) === String(e.source));
      const tgt = papers.find(p => String(p.rank) === String(e.target));
      const h = 26 + Math.abs(x2 - x1) / span * (baseY - 52);
      const dimmed = !(passes(src, null) && passes(tgt, null));
      return `<path class="cite-arc${dimmed ? " dimmed" : ""}" d="M ${x1} ${baseY - 8} Q ${(x1 + x2) / 2} ${baseY - 8 - h}, ${x2} ${baseY - 8}"
        stroke="${colorFor(themeDefs, paperTheme(src))}" data-source="${esc(e.source)}" data-target="${esc(e.target)}"></path>`;
    }).join("");
    const nodes = ordered.map(p => {
      const k = String(p.rank);
      const r = 4 + Math.round(inSetCited(p) / maxIn * 7);
      const dimmed = !passes(p, null);
      return `<circle class="cite-node${core.has(k) ? " core" : ""}${dimmed ? " dimmed" : ""}" cx="${xOf.get(k)}" cy="${baseY}" r="${r}"
          fill="${colorFor(themeDefs, paperTheme(p))}" data-rank="${esc(k)}"></circle>
        <text class="cite-rank" x="${xOf.get(k)}" y="${baseY + 22}">${esc(k)}</text>`;
    }).join("");
    svg.innerHTML = arcs + nodes;
    svg.querySelectorAll(".cite-node").forEach(node => {
      const k = node.dataset.rank;
      const touching = svg.querySelectorAll(`.cite-arc[data-source="${CSS.escape(k)}"], .cite-arc[data-target="${CSS.escape(k)}"]`);
      node.addEventListener("mouseenter", () => touching.forEach(a => a.classList.add("hl")));
      node.addEventListener("mouseleave", () => touching.forEach(a => a.classList.remove("hl")));
      node.addEventListener("click", () => openDetail(k));
      S.bindTip(node, () => {
        const p = papers.find(x => String(x.rank) === k);
        const cites = citeEdges.filter(e => String(e.source) === k).length;
        return `<b>#${esc(k)} ${esc(shortLabel(p.title, 52))}</b><span class="tip-sub">${B("集合内被引", "Cited in set")} ${inSetCited(p)} · ${B("引用集合内", "Cites in set")} ${cites} · ${B("全网被引", "Global citations")} ${p.cited_by_count || 0}</span>`;
      });
    });
    svg.querySelectorAll(".cite-arc").forEach(arc => {
      S.bindTip(arc, () => {
        const src = papers.find(p => String(p.rank) === String(arc.dataset.source));
        const tgt = papers.find(p => String(p.rank) === String(arc.dataset.target));
        return `<b>#${esc(arc.dataset.source)}</b> ${B("引用", "cites")} <b>#${esc(arc.dataset.target)}</b><span class="tip-sub">${esc(shortLabel(src.title, 40))} → ${esc(shortLabel(tgt.title, 40))}</span>`;
      });
      arc.addEventListener("click", () => openDetail(arc.dataset.target));
    });
    renderCiteCore();
  }
  function renderCiteCore() {
    const box = document.getElementById("citeCore");
    const withInSet = papers.filter(p => inSetCited(p) > 0)
      .sort((a, b) => inSetCited(b) - inSetCited(a) || (b.cited_by_count || 0) - (a.cited_by_count || 0));
    const useGlobal = !withInSet.length;
    const rows = (useGlobal
      ? papers.filter(p => (p.cited_by_count || 0) > 0).sort((a, b) => (b.cited_by_count || 0) - (a.cited_by_count || 0))
      : withInSet).slice(0, 5);
    document.getElementById("citeCoreTitle").innerHTML = useGlobal
      ? B("高被引 Top 5（全网）", "Most cited Top 5 (global)")
      : B("核心必读 Top 5", "Core must-reads Top 5");
    box.innerHTML = rows.map(p => `
      <div class="core-item" data-rank="${esc(p.rank)}">
        <div class="cnum">${useGlobal ? (p.cited_by_count || 0) : inSetCited(p)}<span>${useGlobal ? "cited" : "in-set"}</span></div>
        <div><strong>#${esc(p.rank)} ${esc(p.title)}</strong><em>${esc(p.journal || "")}</em></div>
      </div>`).join("") || `<p class="hint">${B("暂无引用数据", "No citation data yet")}</p>`;
    box.querySelectorAll(".core-item").forEach(el => el.addEventListener("click", () => openDetail(el.dataset.rank)));
  }

  function refreshReading() {
    S.renderReadbar(document.getElementById("readbar"), papers, notes);
    renderCards();
  }
  function renderCards() {
    const shown = visiblePapers();
    document.getElementById("cardCount").innerHTML = B(`${shown.length} 篇文章`, `${shown.length} papers`);
    const box = document.getElementById("cards");
    if (!shown.length) {
      box.innerHTML = `<div class="empty">${B("没有匹配的文章，试试清除部分筛选。", "No matching papers; try clearing some filters.")}</div>`;
      return;
    }
    box.innerHTML = shown.map(p => {
      const entry = notes.get(p.rank);
      return `
      <article class="card" role="button" tabindex="0" data-rank="${esc(p.rank)}" style="--pc:${colorFor(themeDefs, paperTheme(p))}">
        <div class="card-eyebrow">
          <span class="rankno">#${esc(p.rank)}</span>
          ${p.is_new ? `<span class="tag new">NEW</span>` : ""}
          <span class="je">${S.highlight(p.journal || "—", state.q)}</span>
          <span class="dt">${esc(p.publication_date || S.yearOf(p) || "")}</span>
          <span class="sp"></span>
          ${(p.in_set_cited || 0) > 0 ? `<span class="tag cited" title="集合内被引 / cited within this collection">被引 ${p.in_set_cited}</span>` : ""}
          ${S.casTagHtml(p)}
          ${p.official_impact_factor ? `<span class="tag if">IF ${esc(p.official_impact_factor)}</span>` : ""}
          ${p.local_pdf_path ? `<span class="tag pdf">PDF</span>` : ""}
        </div>
        <h3>${S.highlight(p.title, state.q)}</h3>
        <p class="card-authors">${S.highlight(S.splitAuthors(p.authors).join(", "), state.q)}</p>
        ${p.abstract ? `<p class="card-abstract">${S.highlight(p.abstract, state.q)}</p>` : ""}
        <div class="card-foot">
          <span class="tag theme">${esc(paperTheme(p))}</span>
          <span class="tag method">${esc(paperMethod(p))}</span>
          <span class="sp"></span>
          ${S.statusChipHtml(p.rank, entry)}
          ${S.starBtnHtml(p.rank, entry)}
        </div>
      </article>`;
    }).join("");
    box.querySelectorAll(".card").forEach(card => {
      card.addEventListener("click", e => {
        if (e.target.closest("[data-read-rank],[data-star-rank]")) return;
        openDetail(card.dataset.rank);
      });
      card.addEventListener("keydown", e => {
        if (e.target !== card) return;
        if (e.key === "Enter" || e.key === " ") { e.preventDefault(); openDetail(card.dataset.rank); }
      });
    });
    box.querySelectorAll("[data-read-rank]").forEach(btn => btn.addEventListener("click", e => {
      e.stopPropagation();
      notes.cycle(btn.dataset.readRank);
      refreshReading();
    }));
    box.querySelectorAll("[data-star-rank]").forEach(btn => btn.addEventListener("click", e => {
      e.stopPropagation();
      const r = btn.dataset.starRank;
      notes.set(r, { star: !notes.get(r).star });
      refreshReading();
    }));
  }

  function renderChips() {
    const bar = document.getElementById("chipBar");
    const chips = [];
    const chip = (label, value, clear) => chips.push({ label, value, clear });
    if (state.q) chip(B("搜索", "Search"), state.q, () => { state.q = ""; document.getElementById("searchInput").value = ""; });
    if (state.theme) chip(B("主题", "Theme"), state.theme, () => { state.theme = null; });
    if (state.method) chip(B("方法", "Method"), state.method, () => { state.method = null; });
    if (state.journal) chip(B("期刊", "Journal"), state.journal, () => { state.journal = null; });
    if (state.month) chip(B("月份", "Month"), state.month, () => { state.month = null; });
    if (state.pdf === "missing") chip(B("缺少 PDF", "Missing PDF"), "", () => { state.pdf = null; });
    if (state.read) chip(state.read === "fresh" ? B("本次新增", "New papers") : B("阅读状态", "Reading"),
      state.read === "fresh" ? "" : state.read, () => { state.read = null; document.getElementById("readSelect").value = ""; });
    if (!chips.length) { bar.hidden = true; bar.innerHTML = ""; return; }
    bar.hidden = false;
    bar.innerHTML = chips.map((c, i) =>
      `<button class="fchip" type="button" data-i="${i}">${c.label}${c.value ? `: <b>${esc(c.value)}</b>` : ""}<span class="x">×</span></button>`).join("")
      + `<button class="fchip clear" type="button" id="chipClear">${B("清除全部", "Clear all")}</button>`;
    bar.querySelectorAll(".fchip[data-i]").forEach(btn => btn.addEventListener("click", () => { chips[Number(btn.dataset.i)].clear(); renderAll(); }));
    document.getElementById("chipClear").addEventListener("click", clearFilters);
  }

  function syncHash() {
    S.writeHash({
      q: state.q || null, theme: state.theme, method: state.method, journal: state.journal,
      month: state.month, pdf: state.pdf, read: state.read, sort: state.sort !== "rank" ? state.sort : null, paper: activeRank,
    });
  }
  function animateFirstPaint() {
    if (S.reduced) return;
    document.querySelectorAll("#journalBars .fill").forEach(el => {
      const value = el.style.width;
      el.style.width = "0%";
      requestAnimationFrame(() => requestAnimationFrame(() => { el.style.width = value; }));
    });
    document.querySelectorAll("#timeline .tl-fill").forEach(el => {
      const value = el.style.height;
      el.style.height = "0%";
      requestAnimationFrame(() => requestAnimationFrame(() => { el.style.height = value; }));
    });
  }
  function renderAll() {
    renderCategory("theme");
    renderCategory("method");
    renderRelation();
    renderCitations();
    renderTimeline();
    renderJournals();
    renderCards();
    renderChips();
    S.renderReadbar(document.getElementById("readbar"), papers, notes);
    document.getElementById("kpiPdf").setAttribute("aria-pressed", state.pdf === "missing");
    if (!booted) { booted = true; animateFirstPaint(); }
    syncHash();
  }

  function paperTags(p) {
    return [
      ["theme", paperTheme(p)],
      ["method", paperMethod(p)],
      ["if", p.official_impact_factor ? `IF ${p.official_impact_factor}` : ""],
    ].filter(([, text]) => text);
  }
  function detailFactRows(p) {
    const rows = [
      [B("期刊", "Journal"), p.journal || "—"],
      [B("发表日期", "Date"), p.publication_date || "—"],
      [B("文章类型", "Type"), p.article_type || "—"],
      [B("官方 IF", "Official IF"), p.official_impact_factor || "—"],
      [B("主题", "Theme"), paperTheme(p)],
      [B("方法", "Method"), paperMethod(p)],
    ];
    if (S.casTier(p)) rows.push([B("中科院分区", "CAS Tier"), S.casLabel(p)]);
    if (inSetCited(p) > 0 || (p.cited_by_count || 0) > 0) {
      rows.push([B("被引", "Citations"), `${inSetCited(p)} in-set · ${p.cited_by_count || 0} global`]);
    }
    return rows;
  }
  function openDetail(rank) {
    const paper = papers.find(p => String(p.rank) === String(rank));
    if (!paper) return;
    const wasOpen = !!activeRank;
    activeRank = String(rank);
    navList = visiblePapers();
    let idx = navList.findIndex(p => String(p.rank) === activeRank);
    if (idx === -1) { navList = sortPapers(papers.slice()); idx = navList.findIndex(p => String(p.rank) === activeRank); }
    const detail = details[activeRank] || {};
    document.getElementById("detailCard").style.setProperty("--dc", colorFor(themeDefs, paperTheme(paper)));
    document.getElementById("detailEyebrow").textContent = `Rank ${paper.rank} · ${paperTheme(paper)} · ${paper.article_type || "research article"}`;
    document.getElementById("detailTitle").textContent = paper.title;
    document.getElementById("detailTags").innerHTML = paperTags(paper).map(([cls, text]) => `<span class="tag ${cls}">${esc(text)}</span>`).join("")
      + (paper.local_pdf_path ? `<span class="tag pdf">PDF</span>` : "");
    document.getElementById("detailFacts").innerHTML = detailFactRows(paper)
      .map(([label, value]) => `<div class="detail-fact"><span>${label}</span><strong>${esc(value)}</strong></div>`).join("");
    document.getElementById("detailSections").innerHTML = [
      S.detailSection(B("研究主题", "Research Theme"), detail.topic),
      S.detailSection(B("方法", "Method"), detail.method),
      S.detailSection(B("数据或案例", "Data or Case"), detail.data),
      S.detailSection(B("主要结果", "Findings"), detail.findings),
      S.detailSection(B("局限", "Limitations"), detail.limits),
      S.detailSection(B("为什么重要", "Relevance"), detail.relevance),
    ].join("");
    const notesBox = document.getElementById("detailNotes");
    notesBox.innerHTML = S.notesPanelHtml(activeRank, notes.get(activeRank));
    S.bindNotesPanel(notesBox, activeRank, notes, quiet => {
      S.renderReadbar(document.getElementById("readbar"), papers, notes);
      if (!quiet) renderCards();
    });
    const pdfHref = S.fileUrl(paper.local_pdf_path);
    document.getElementById("detailLinks").innerHTML = [
      paper.doi ? `<a class="detail-link" href="${esc(paper.doi)}" target="_blank" rel="noopener">${B("打开 DOI", "Open DOI")}</a>` : "",
      pdfHref ? `<button class="detail-link" type="button" id="openPdfLauncher">${B("打开本地 PDF", "Open local PDF")}</button>` : "",
      paper.zotero_item_key ? `<a class="detail-link" href="zotero://select/library/items/${esc(paper.zotero_item_key)}" title="Zotero 桌面版需已启动 / Zotero desktop must be running">${B("在 Zotero 中打开", "Open in Zotero")}</a>` : "",
      `<button class="detail-link" type="button" id="copyApa">${B("复制 APA 引用", "Copy APA")}</button>`,
      `<button class="detail-link" type="button" id="copyBib">${B("复制 BibTeX", "Copy BibTeX")}</button>`,
    ].filter(Boolean).join("");
    const pdfButton = document.getElementById("openPdfLauncher");
    if (pdfButton) pdfButton.addEventListener("click", () => window.location.assign(pdfLauncherUrl(paper)));
    document.getElementById("copyApa").addEventListener("click", e => S.copyText(S.apa(paper), e.currentTarget, B("已复制", "Copied")));
    document.getElementById("copyBib").addEventListener("click", e => S.copyText(S.bibtex(paper), e.currentTarget, B("已复制", "Copied")));
    document.getElementById("detailPrev").disabled = idx <= 0;
    document.getElementById("detailNext").disabled = idx < 0 || idx >= navList.length - 1;
    const shell = document.getElementById("detailShell");
    shell.classList.add("open");
    shell.setAttribute("aria-hidden", "false");
    document.body.style.overflow = "hidden";
    if (!wasOpen) releaseFocus = S.trapFocus(shell.querySelector(".detail-card"));
    syncHash();
  }
  function closeDetail() {
    const shell = document.getElementById("detailShell");
    if (!shell.classList.contains("open")) return;
    shell.classList.remove("open");
    shell.setAttribute("aria-hidden", "true");
    document.body.style.overflow = "";
    activeRank = null;
    if (releaseFocus) { releaseFocus(); releaseFocus = null; }
    renderCards();
    syncHash();
  }
  function moveDetail(delta) {
    const idx = navList.findIndex(p => String(p.rank) === String(activeRank));
    const next = navList[idx + delta];
    if (next) openDetail(next.rank);
  }

  function applyHash() {
    const h = S.readHash();
    state.q = h.q || "";
    state.theme = h.theme || null;
    state.method = h.method || null;
    state.journal = h.journal || null;
    state.month = h.month || null;
    state.pdf = h.pdf === "missing" ? "missing" : null;
    state.read = ["unread", "reading", "read", "starred", "fresh"].includes(h.read) ? h.read : null;
    state.sort = ["rank", "year", "if", "cited"].includes(h.sort) ? h.sort : "rank";
    document.getElementById("searchInput").value = state.q;
    document.getElementById("readSelect").value = state.read || "";
    document.getElementById("sortSelect").value = state.sort;
    renderAll();
    if (h.paper) openDetail(h.paper); else closeDetail();
  }

  document.getElementById("dashTitle").textContent = spec.title || "Literature Review Dashboard";
  document.getElementById("dashSubtitle").textContent = spec.subtitle || "";
  S.countUp(document.getElementById("paperCount"), papers.length);
  S.countUp(document.getElementById("themeKpi"), themeDefs.length);
  S.countUp(document.getElementById("methodKpi"), methodDefs.length);
  if ((data.new_count || 0) > 0) {
    document.querySelector("#kpiPapers .note").insertAdjacentHTML("beforeend",
      ` <span class="tag new" title="本次构建新增 / added in this build">+${data.new_count} NEW</span>`);
  }
  const pdfN = papers.filter(p => p.local_pdf_path).length;
  document.getElementById("pdfKpi").textContent = `${pdfN}/${papers.length}`;
  S.initTheme(document.getElementById("themeToggle"));
  S.initLang(document.getElementById("langToggle"));
  S.bindSlashFocus(document.getElementById("searchInput"));
  buildTimeline();

  function shareCardConfig() {
    const themeCounts = new Map();
    papers.forEach(p => themeCounts.set(paperTheme(p), (themeCounts.get(paperTheme(p)) || 0) + 1));
    const themes = themeDefs
      .map(d => ({ name: d.name, count: themeCounts.get(d.name) || 0, hex: S.resolveHexLight(d.color) }))
      .filter(t => t.count > 0);
    const journalMap = new Map();
    papers.forEach(p => {
      const j = p.journal || "";
      if (!j) return;
      if (!journalMap.has(j)) journalMap.set(j, { name: j, count: 0, ifValue: 0, cas: "" });
      const row = journalMap.get(j);
      row.count += 1;
      row.ifValue = Math.max(row.ifValue, Number(p.official_impact_factor) || 0);
      if (!row.cas) row.cas = S.casLabel(p);
    });
    const journals = [...journalMap.values()]
      .sort((a, b) => b.ifValue - a.ifValue || b.count - a.count)
      .slice(0, 3)
      .map(r => ({ name: r.name, count: r.count, if: r.ifValue ? r.ifValue.toFixed(1) : "", cas: r.cas }));
    return { title: spec.title || "Literature Review", papers: papers.length, themes, journals,
      read: notes.counts(papers), newCount: data.new_count || 0 };
  }
  document.getElementById("shareCard").addEventListener("click", e => S.exportShareCard(shareCardConfig(), e.currentTarget));

  document.getElementById("searchInput").addEventListener("input", S.debounce(e => { state.q = e.target.value.trim(); renderAll(); }, 160));
  document.getElementById("sortSelect").addEventListener("change", e => { state.sort = e.target.value; renderCards(); syncHash(); });
  document.getElementById("readSelect").addEventListener("change", e => { state.read = e.target.value || null; renderAll(); });
  document.getElementById("exportCsv").addEventListener("click", () => {
    S.download("literature-export.csv", S.csv(visiblePapers(), [
      ["rank", p => p.rank], ["title", p => p.title], ["authors", p => p.authors], ["journal", p => p.journal],
      ["date", p => p.publication_date], ["year", p => S.yearOf(p)], ["doi", p => p.doi],
      ["theme", p => paperTheme(p)], ["subtheme", p => paperSubtheme(p)], ["method", p => paperMethod(p)],
      ["impact_factor", p => p.official_impact_factor], ["cas_partition", p => S.casLabel(p)],
      ["cited_in_set", p => inSetCited(p) || ""], ["cited_global", p => p.cited_by_count || ""],
      ["is_new", p => p.is_new ? "1" : ""], ["local_pdf", p => p.local_pdf_path],
      ["read_status", p => notes.get(p.rank).s || "unread"], ["starred", p => notes.get(p.rank).star ? "1" : ""],
      ["my_note", p => notes.get(p.rank).note || ""],
    ]), "text/csv;charset=utf-8");
  });
  document.getElementById("exportZotero").addEventListener("click", () => S.exportWriteback({
    title: spec.title, papers, notes, themeOf: paperTheme, subthemeOf: paperSubtheme, methodOf: paperMethod,
  }));
  document.getElementById("exportBib").addEventListener("click", () => {
    S.download("literature-export.bib", visiblePapers().map(S.bibtex).join("\n\n") + "\n", "text/plain;charset=utf-8");
  });
  document.getElementById("kpiPapers").addEventListener("click", clearFilters);
  document.getElementById("kpiPapers").addEventListener("keydown", e => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); clearFilters(); } });
  const kpiPdf = document.getElementById("kpiPdf");
  const togglePdfFilter = () => { state.pdf = state.pdf === "missing" ? null : "missing"; renderAll(); };
  kpiPdf.addEventListener("click", togglePdfFilter);
  kpiPdf.addEventListener("keydown", e => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); togglePdfFilter(); } });
  document.getElementById("detailClose").addEventListener("click", closeDetail);
  document.getElementById("detailPrev").addEventListener("click", () => moveDetail(-1));
  document.getElementById("detailNext").addEventListener("click", () => moveDetail(1));
  document.getElementById("detailShell").addEventListener("click", e => { if (e.target.id === "detailShell") closeDetail(); });
  document.addEventListener("keydown", e => {
    const tag = (e.target.tagName || "").toLowerCase();
    if (e.key === "Escape") closeDetail();
    if (!document.getElementById("detailShell").classList.contains("open")) return;
    if (tag === "input" || tag === "select" || tag === "textarea") return;
    if (e.key === "ArrowLeft") { e.preventDefault(); moveDetail(-1); }
    if (e.key === "ArrowRight") { e.preventDefault(); moveDetail(1); }
  });
  window.addEventListener("hashchange", applyHash);
  applyHash();
  S.mountShareCardPreview(shareCardConfig);
</script>
</body>
</html>
"""

DASHBOARD_HTML = (
    DASHBOARD_HTML
    .replace("__THEME_BOOT__", THEME_BOOT_JS)
    .replace("__SHARED_CSS__", SHARED_CSS)
    .replace("__SHARED_JS__", SHARED_JS)
)


def build_dashboard(args: argparse.Namespace) -> None:
    papers_path = Path(args.papers)
    payload = read_payload(papers_path)
    papers = normalize_papers(payload.get("papers", []), args.limit)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    dashboard_file = args.dashboard_name if args.dashboard_name.endswith(".html") else f"{args.dashboard_name}.html"
    data_file = Path(dashboard_file).with_suffix("").name + "-data.js"
    details_file = Path(dashboard_file).with_suffix("").name + "-details.js"
    pdf_open_file = Path(dashboard_file).with_suffix("").name + "-pdf-open.html"
    title = args.title or clean_text(payload.get("config", {}).get("topic")) or "Systematic Literature Review"
    subtitle = args.subtitle or "Bilingual classification, article notes, journal evidence, and local PDF links."
    spec = load_spec(Path(args.spec), papers, title, subtitle)
    if getattr(args, "no_snapshot", False):
        delta = {"had_baseline": False, "new_papers": [], "removed": []}
        for paper in papers:
            paper["is_new"] = False
    else:
        delta = apply_delta_tracking(papers, papers_path.parent / "dashboard-snapshot.json")
        if write_update_digest(output_dir / "update-digest.md", delta, len(papers), spec["title"]):
            print(str((output_dir / "update-digest.md").resolve()))
    citations = load_citation_network(papers_path)
    data_payload = {
        "config": payload.get("config", {}),
        "papers": papers,
        "spec": {key: spec[key] for key in ("title", "subtitle", "layout", "theme_definitions", "subtheme_definitions", "method_definitions", "paper_assignments")},
        "new_count": len(delta.get("new_papers") or []),
    }
    if citations:
        data_payload["citations"] = citations
    inline = bool(getattr(args, "inline", False))
    if spec.get("layout") == "large-library":
        write_large_library_dashboard(
            output_dir=output_dir,
            dashboard_file=dashboard_file,
            data_file=data_file,
            details_file=details_file,
            pdf_open_file=pdf_open_file,
            data_payload=data_payload,
            details=spec.get("details", {}),
            inline=inline,
        )
        print(str((output_dir / dashboard_file).resolve()))
        return
    # The external data files are always written: the PDF launcher page reads
    # them, and Codex reuses them when refining the spec. --inline additionally
    # embeds the same payloads in the main HTML so that one file can be shared.
    write_js(output_dir / data_file, "__SLR_DASHBOARD_DATA__", data_payload)
    write_js(output_dir / details_file, "__SLR_DASHBOARD_DETAILS__", spec.get("details", {}))
    if inline:
        data_script = inline_js_tag("__SLR_DASHBOARD_DATA__", data_payload)
        details_script = inline_js_tag("__SLR_DASHBOARD_DETAILS__", spec.get("details", {}))
    else:
        data_script = f'<script src="{data_file}"></script>'
        details_script = f'<script src="{details_file}"></script>'
    (output_dir / dashboard_file).write_text(
        DASHBOARD_HTML.replace("__DATA_SCRIPT__", data_script)
        .replace("__DETAILS_SCRIPT__", details_script)
        .replace("__PDF_OPEN_FILE__", pdf_open_file),
        encoding="utf-8",
    )
    (output_dir / pdf_open_file).write_text(
        PDF_OPEN_HTML.replace("__DATA_FILE__", data_file).replace("__DASHBOARD_FILE__", dashboard_file),
        encoding="utf-8",
    )
    print(str((output_dir / dashboard_file).resolve()))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a literature review dashboard from papers.json and dashboard-spec.json.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init-spec", help="Create a starter dashboard-spec.json for manual/Codex refinement.")
    init.add_argument("--papers", required=True, help="Path to metadata/papers.json, all-candidates.json, or dashboard data JS.")
    init.add_argument("--output", required=True)
    init.add_argument("--title", default="Systematic Literature Review Dashboard")
    init.add_argument("--subtitle", default="Bilingual classification, article notes, journal evidence, and local PDF links.")
    init.add_argument("--limit", type=int, default=None)
    init.set_defaults(func=init_spec)

    build = subparsers.add_parser("build", help="Render the dashboard HTML/JS files.")
    build.add_argument("--papers", required=True)
    build.add_argument("--spec", required=True)
    build.add_argument("--output-dir", required=True)
    build.add_argument("--dashboard-name", default="literature-dashboard")
    build.add_argument("--title", default="")
    build.add_argument("--subtitle", default="")
    build.add_argument("--limit", type=int, default=None)
    build.add_argument("--inline", action="store_true",
                       help="Embed papers and details inside the dashboard HTML so the single file can be shared (local PDF links still only work on this machine).")
    build.add_argument("--no-snapshot", action="store_true",
                       help="Skip NEW-paper delta tracking and the update digest (no dashboard-snapshot.json read/write). Use for throwaway smoke builds.")
    build.set_defaults(func=build_dashboard)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
