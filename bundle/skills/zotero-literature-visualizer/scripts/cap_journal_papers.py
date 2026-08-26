# //============XJQ(本次修改：提供每个期刊最多保留指定篇数的确定性限额模块）====================//
"""Cap a literature candidate set to a deterministic maximum per journal.

The helper works only on title/abstract/open-metadata records. It keeps the
existing rank order when one is available, so applying a journal cap does not
silently replace the review's ranking policy. The returned records retain
their original rank; callers that publish a new set can use ``renumber_ranks``
after remapping any dashboard detail records.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import OrderedDict
from datetime import date
from pathlib import Path
from typing import Any, Iterable


MISSING_JOURNAL = "Metadata missing / 未提供"
_MISSING_RANK = 10**12


def normalize_journal(value: Any) -> str:
    """Collapse whitespace and provide an explicit label for missing journals."""
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    return text or MISSING_JOURNAL


def _rank_number(paper: dict[str, Any]) -> int | None:
    try:
        value = int(paper.get("rank"))
    except (TypeError, ValueError):
        return None
    return value if value > 0 else None


def _date_number(paper: dict[str, Any]) -> int:
    value = str(paper.get("publication_date") or "")[:10]
    try:
        return date.fromisoformat(value).toordinal()
    except ValueError:
        return 0


def _fallback_sort_key(paper: dict[str, Any]) -> tuple[Any, ...]:
    """Use recency/relevance only when a record has no usable rank."""
    return (
        -_date_number(paper),
        -int(paper.get("relevance_score") or 0),
        -int(paper.get("cited_by_count") or 0),
        str(paper.get("title") or "").casefold(),
        str(paper.get("doi") or "").casefold(),
    )


def _selection_key(paper: dict[str, Any]) -> tuple[Any, ...]:
    rank = _rank_number(paper)
    if rank is not None:
        return (0, rank, "", "", str(paper.get("title") or "").casefold(), str(paper.get("doi") or "").casefold())
    return (1, *_fallback_sort_key(paper))


def _global_sort_key(paper: dict[str, Any]) -> tuple[Any, ...]:
    rank = _rank_number(paper)
    if rank is not None:
        return (0, rank, "", "")
    return (1, *_fallback_sort_key(paper))


def cap_papers_by_journal(
    papers: Iterable[dict[str, Any]],
    max_per_journal: int = 10,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Return records with no journal group exceeding ``max_per_journal``.

    Journal grouping is case-insensitive after whitespace normalization. The
    first display spelling is retained in the summary, and missing journals
    are counted under ``Metadata missing / 未提供``.
    """
    if int(max_per_journal) < 1:
        raise ValueError("max_per_journal must be at least 1")

    groups: OrderedDict[str, list[tuple[str, dict[str, Any]]]] = OrderedDict()
    display_names: dict[str, str] = {}
    rows = [dict(paper) for paper in papers if isinstance(paper, dict)]
    for paper in rows:
        label = normalize_journal(paper.get("journal"))
        key = label.casefold()
        display_names.setdefault(key, label)
        groups.setdefault(key, []).append((label, paper))

    selected: list[dict[str, Any]] = []
    journal_summary: OrderedDict[str, dict[str, int]] = OrderedDict()
    kept_ranks: list[Any] = []
    removed_ranks: list[Any] = []
    for key, entries in groups.items():
        ordered = sorted(entries, key=lambda item: _selection_key(item[1]))
        chosen = ordered[: int(max_per_journal)]
        label = display_names[key]
        for _, paper in chosen:
            output = dict(paper)
            output["journal"] = normalize_journal(output.get("journal"))
            selected.append(output)
            kept_ranks.append(output.get("rank"))
        for _, paper in ordered[int(max_per_journal) :]:
            removed_ranks.append(paper.get("rank"))
        journal_summary[label] = {
            "before": len(entries),
            "after": len(chosen),
            "removed": len(entries) - len(chosen),
        }

    selected.sort(key=_global_sort_key)
    summary = {
        "max_per_journal": int(max_per_journal),
        "before_total": len(rows),
        "after_total": len(selected),
        "removed_total": len(rows) - len(selected),
        "selection_policy": "Keep the existing positive rank order; records without rank use publication date, relevance score, citation count, title, then DOI as deterministic tie-breakers.",
        "journals": journal_summary,
        "kept_ranks": kept_ranks,
        "removed_ranks": removed_ranks,
    }
    return selected, summary


def renumber_ranks(papers: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return copies with contiguous 1-based ranks while preserving order."""
    result = []
    for rank, paper in enumerate(papers, start=1):
        output = dict(paper)
        output["rank"] = rank
        result.append(output)
    return result


def _load_payload(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _write_payload(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Cap literature records per journal.")
    parser.add_argument("--input", required=True, help="Input papers JSON containing a papers array.")
    parser.add_argument("--output", required=True, help="Output JSON path.")
    parser.add_argument("--summary", required=True, help="JSON path for the cap summary.")
    parser.add_argument("--max-per-journal", type=int, default=10)
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    summary_path = Path(args.summary)
    payload = _load_payload(input_path)
    selected, summary = cap_papers_by_journal(payload.get("papers", []), args.max_per_journal)
    config = dict(payload.get("config") or {})
    config["max_papers_per_journal"] = int(args.max_per_journal)
    config["journal_cap_selection_policy"] = summary["selection_policy"]
    output_payload = dict(payload)
    output_payload["config"] = config
    output_payload["papers"] = renumber_ranks(selected)
    _write_payload(output_path, output_payload)
    summary["input"] = str(input_path)
    summary["output"] = str(output_path)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"before": summary["before_total"], "after": summary["after_total"], "removed": summary["removed_total"], "max_per_journal": args.max_per_journal}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# //================XJQ(本次修改：提供每个期刊最多保留指定篇数的确定性限额模块 END===============//
