#!/usr/bin/env python3
"""Link dashboard papers to the user's local Zotero items without any API key.

Reads a temporary snapshot of zotero.sqlite (Zotero may stay open; the
original database is never modified), matches metadata/papers.json rows by
DOI first and normalized title second, and writes back:

- zotero_item_key   -> the dashboard shows an "Open in Zotero" link
                        (zotero://select/library/items/<key>)
- local_pdf_path    -> filled when the Zotero item has a local PDF attachment
                        and the paper does not already have a PDF path

Rebuild the dashboard afterwards. Typical use: after the user imports the
review's RIS/BibTeX package (or after zotero_api_import.py import-manifest),
so every dashboard card can jump to its Zotero item and open its PDF.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sqlite3
import tempfile
from pathlib import Path
from typing import Any


def clean_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def normalize_doi(value: Any) -> str:
    doi = clean_text(value).lower()
    return re.sub(r"^https?://(dx\.)?doi\.org/", "", doi)


def normalize_title(value: Any) -> str:
    return re.sub(r"[^a-z0-9一-鿿]+", "", clean_text(value).lower())[:140]


def default_zotero_dir() -> Path:
    for candidate in (Path.home() / "Zotero", Path(os.environ.get("ZOTERO_DATA_DIR", ""))):
        if candidate and (candidate / "zotero.sqlite").exists():
            return candidate
    raise SystemExit("Could not find Zotero data directory. Pass --zotero-dir with the folder containing zotero.sqlite.")


def resolve_pdf_path(zotero_dir: Path, attachment_key: str, raw_path: str) -> Path | None:
    raw_path = clean_text(raw_path)
    if not raw_path:
        return None
    storage_dir = zotero_dir / "storage" / attachment_key
    if raw_path.startswith(("storage:", "attachments:")):
        candidate = storage_dir / raw_path.split(":", 1)[1]
        if candidate.exists():
            return candidate
        pdfs = sorted(storage_dir.glob("*.pdf")) if storage_dir.exists() else []
        return pdfs[0] if pdfs else None
    candidate = Path(raw_path)
    return candidate if candidate.exists() else None


def load_zotero_index(zotero_dir: Path) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    """Return (by_doi, by_title) maps of {key, itemID, pdf_path}. Uses a snapshot copy."""
    temp_dir = Path(tempfile.mkdtemp(prefix="slr-zotero-link-"))
    try:
        snapshot = temp_dir / "zotero.sqlite"
        shutil.copy2(zotero_dir / "zotero.sqlite", snapshot)
        con = sqlite3.connect(f"file:{snapshot.as_posix()}?mode=ro", uri=True)
        con.row_factory = sqlite3.Row
        rows = con.execute(
            """
            select i.itemID, i.key, f.fieldName, v.value
            from items i
            join itemData d on d.itemID = i.itemID
            join fields f on f.fieldID = d.fieldID
            join itemDataValues v on v.valueID = d.valueID
            where f.fieldName in ('DOI', 'title')
              and i.itemID not in (select itemID from deletedItems)
            """
        ).fetchall()
        items: dict[int, dict[str, Any]] = {}
        for row in rows:
            entry = items.setdefault(int(row["itemID"]), {"key": row["key"], "itemID": int(row["itemID"]), "doi": "", "title": "", "pdf_path": ""})
            if row["fieldName"] == "DOI":
                entry["doi"] = normalize_doi(row["value"])
            else:
                entry["title"] = clean_text(row["value"])
        attachments = con.execute(
            """
            select ia.parentItemID, ia.path, attachment.key as attachmentKey
            from itemAttachments ia
            join items attachment on attachment.itemID = ia.itemID
            where ia.contentType = 'application/pdf' and ia.parentItemID is not null
            order by ia.itemID
            """
        ).fetchall()
        for row in attachments:
            parent = items.get(int(row["parentItemID"]))
            if not parent or parent["pdf_path"]:
                continue
            path = resolve_pdf_path(zotero_dir, str(row["attachmentKey"]), str(row["path"] or ""))
            if path:
                parent["pdf_path"] = str(path)
        con.close()
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
    by_doi = {entry["doi"]: entry for entry in items.values() if entry["doi"]}
    by_title = {normalize_title(entry["title"]): entry for entry in items.values() if entry["title"]}
    return by_doi, by_title


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fill zotero_item_key (and local PDF paths) in papers.json from the local Zotero database.")
    parser.add_argument("--papers", required=True, help="Path to metadata/papers.json.")
    parser.add_argument("--zotero-dir", help="Folder containing zotero.sqlite (default: ~/Zotero or ZOTERO_DATA_DIR).")
    parser.add_argument("--dry-run", action="store_true", help="Report matches without writing papers.json.")
    parser.add_argument("--overwrite-pdf", action="store_true", help="Replace existing local_pdf_path values with the Zotero attachment path.")
    args = parser.parse_args(argv)

    papers_path = Path(args.papers).resolve()
    payload = json.loads(papers_path.read_text(encoding="utf-8-sig"))
    rows = payload.get("papers") if isinstance(payload, dict) else payload
    if not isinstance(rows, list):
        raise SystemExit(f"{papers_path} does not contain a papers list")
    zotero_dir = Path(args.zotero_dir).expanduser() if args.zotero_dir else default_zotero_dir()
    by_doi, by_title = load_zotero_index(zotero_dir)

    matched = linked_pdf = 0
    report: list[str] = []
    for row in rows:
        doi = normalize_doi(row.get("doi_url") or row.get("doi"))
        hit = by_doi.get(doi) if doi else None
        how = "doi"
        if not hit:
            hit = by_title.get(normalize_title(row.get("title")))
            how = "title"
        if not hit:
            row.pop("zotero_item_key", None) if row.get("zotero_item_key") == "" else None
            report.append(f"  - not in Zotero: #{row.get('rank')} {clean_text(row.get('title'))[:70]}")
            continue
        matched += 1
        row["zotero_item_key"] = hit["key"]
        if hit["pdf_path"] and (args.overwrite_pdf or not clean_text(row.get("local_pdf_path"))):
            row["local_pdf_path"] = hit["pdf_path"]
            linked_pdf += 1
        report.append(f"  + #{row.get('rank')} -> {hit['key']} ({how}{', pdf' if hit['pdf_path'] else ''})")

    print(f"Zotero items indexed: {len(by_doi)} with DOI / {len(by_title)} with title")
    print(f"Matched {matched}/{len(rows)} papers; linked {linked_pdf} local PDFs.")
    print("\n".join(report))
    if args.dry_run:
        print("Dry run: papers.json not modified.")
        return 0
    papers_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Updated {papers_path}. Rebuild the dashboard to show 'Open in Zotero' links.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
