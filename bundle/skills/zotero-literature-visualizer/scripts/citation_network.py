#!/usr/bin/env python3
"""Build an in-collection citation network from OpenAlex metadata.

For every paper in metadata/papers.json that has a DOI, this script fetches
its OpenAlex record (id, referenced_works, cited_by_count) in batched
requests, keeps only citation edges where BOTH ends are inside the
collection, and writes metadata/citation-network.json. By default it also
merges cited_by_count / in_set_cited back into papers.json so the next
dashboard build shows citation badges, the arc network, and the core
must-reads list.

Only public OpenAlex metadata is used; no full texts are fetched. Rebuild the
dashboard after running this script.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

OPENALEX_WORKS = "https://api.openalex.org/works"
USER_AGENT = "zotero-literature-visualizer-citations/1.0"
BATCH_SIZE = 40


def http_json(url: str, *, retries: int = 3, sleep: float = 1.0) -> Any:
    last_error: str | None = None
    for attempt in range(1, retries + 1):
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            last_error = f"HTTP {exc.code} for {url}"
            if exc.code in {429, 500, 502, 503, 504} and attempt < retries:
                retry_after = exc.headers.get("Retry-After")
                wait = float(retry_after) if retry_after and retry_after.isdigit() else sleep * attempt
                time.sleep(wait)
                continue
            raise RuntimeError(last_error) from exc
        except (urllib.error.URLError, TimeoutError) as exc:
            last_error = f"{type(exc).__name__}: {exc}"
            if attempt < retries:
                time.sleep(sleep * attempt)
                continue
            raise RuntimeError(last_error) from exc
    raise RuntimeError(last_error or f"Failed to fetch {url}")


def normalize_doi(value: Any) -> str:
    doi = str(value or "").strip().lower()
    doi = re.sub(r"^https?://(dx\.)?doi\.org/", "", doi)
    return doi


def load_papers(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    rows = payload.get("papers") if isinstance(payload, dict) else payload
    if not isinstance(rows, list):
        raise SystemExit(f"{path} does not contain a papers list")
    return (payload if isinstance(payload, dict) else {"papers": rows}), rows


def chunked(items: list[str], size: int) -> list[list[str]]:
    return [items[i : i + size] for i in range(0, len(items), size)]


def fetch_openalex_records(dois: list[str], mailto: str, sleep: float) -> dict[str, dict[str, Any]]:
    """Return {normalized_doi: openalex_record} for every DOI OpenAlex knows."""
    records: dict[str, dict[str, Any]] = {}
    for batch in chunked(dois, BATCH_SIZE):
        params = {
            "filter": "doi:" + "|".join(batch),
            "per-page": str(max(len(batch), 25)),
            "select": "id,doi,referenced_works,cited_by_count,title",
        }
        if mailto:
            params["mailto"] = mailto
        url = f"{OPENALEX_WORKS}?{urllib.parse.urlencode(params)}"
        try:
            payload = http_json(url)
        except RuntimeError as exc:
            print(f"WARN: batch fetch failed ({exc}); skipping {len(batch)} DOIs")
            continue
        for record in payload.get("results", []):
            doi = normalize_doi(record.get("doi"))
            if doi:
                records[doi] = record
        time.sleep(sleep)
    return records


def build_network(args: argparse.Namespace) -> int:
    papers_path = Path(args.papers).resolve()
    payload, rows = load_papers(papers_path)
    mailto = args.mailto or os.environ.get("LITERATURE_REVIEW_EMAIL", "")

    doi_to_rank: dict[str, str] = {}
    for row in rows:
        doi = normalize_doi(row.get("doi") or row.get("doi_url") or row.get("DOI"))
        rank = str(row.get("rank") or "").strip()
        if doi and rank:
            doi_to_rank.setdefault(doi, rank)
    if not doi_to_rank:
        raise SystemExit("No papers with DOIs found; the citation network needs DOIs.")

    print(f"Fetching OpenAlex records for {len(doi_to_rank)} DOIs...")
    records = fetch_openalex_records(list(doi_to_rank), mailto, args.sleep)
    print(f"Matched {len(records)}/{len(doi_to_rank)} DOIs on OpenAlex.")

    openalex_to_rank = {
        str(record.get("id") or ""): doi_to_rank[doi]
        for doi, record in records.items()
        if record.get("id")
    }
    edges: list[dict[str, str]] = []
    seen_edges: set[tuple[str, str]] = set()
    for doi, record in records.items():
        source_rank = doi_to_rank[doi]
        for referenced in record.get("referenced_works") or []:
            target_rank = openalex_to_rank.get(str(referenced))
            if not target_rank or target_rank == source_rank:
                continue
            pair = (source_rank, target_rank)
            if pair in seen_edges:
                continue
            seen_edges.add(pair)
            edges.append({"source": source_rank, "target": target_rank})

    in_set: dict[str, int] = {}
    for edge in edges:
        in_set[edge["target"]] = in_set.get(edge["target"], 0) + 1

    nodes = []
    for doi, record in records.items():
        rank = doi_to_rank[doi]
        nodes.append(
            {
                "rank": rank,
                "doi": doi,
                "openalex_id": record.get("id") or "",
                "cited_by_count": int(record.get("cited_by_count") or 0),
                "in_set_cited": in_set.get(rank, 0),
            }
        )

    output_path = Path(args.output).resolve() if args.output else papers_path.parent / "citation-network.json"
    network = {
        "generated_at": dt.datetime.now().isoformat(timespec="seconds"),
        "source": "OpenAlex referenced_works (public metadata only)",
        "coverage": {"papers": len(rows), "with_doi": len(doi_to_rank), "matched": len(records)},
        "nodes": nodes,
        "edges": edges,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(network, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Edges within the collection: {len(edges)}")
    print(str(output_path))

    if not args.no_update_papers:
        by_rank = {node["rank"]: node for node in nodes}
        updated = 0
        for row in rows:
            node = by_rank.get(str(row.get("rank") or "").strip())
            if not node:
                continue
            row["cited_by_count"] = node["cited_by_count"]
            row["in_set_cited"] = node["in_set_cited"]
            updated += 1
        papers_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Merged citation counts into {updated} rows of {papers_path.name}. Rebuild the dashboard to show them.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fetch in-collection citation edges from OpenAlex and merge counts into papers.json.")
    parser.add_argument("--papers", required=True, help="Path to metadata/papers.json.")
    parser.add_argument("--output", help="Output path (default: citation-network.json next to papers.json).")
    parser.add_argument("--mailto", default="", help="Contact email for the OpenAlex polite pool (or set LITERATURE_REVIEW_EMAIL).")
    parser.add_argument("--sleep", type=float, default=0.25, help="Pause between batched requests, in seconds.")
    parser.add_argument("--no-update-papers", action="store_true", help="Do not write cited_by_count/in_set_cited back into papers.json.")
    parser.set_defaults(func=build_network)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
