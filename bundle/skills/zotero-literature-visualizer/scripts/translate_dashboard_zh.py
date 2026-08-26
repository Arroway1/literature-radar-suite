# //============XJQ(本次修改：为 dashboard 提供真正中文的逐篇证据翻译和离线安全回退）====================//
"""Translate dashboard English evidence into Chinese without altering EN evidence.

The translation route uses public metadata only and an unauthenticated public
translation endpoint. No account, password, cookie, PDF, or publisher session
is accessed. If the endpoint is unavailable, the ZH field receives a Chinese
fallback instead of leaking the English source into ZH.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Callable


FIELDS = ("topic", "method", "data", "findings", "limits", "relevance")
TRANSLATABLE_FIELDS = FIELDS
MARKER_PREFIX = "ZZZTRANSLATEFIELD"
FALLBACKS = {
    "topic": "中文主题翻译暂不可用；请查看英文证据字段。",
    "method": "中文方法翻译暂不可用；请查看英文证据字段。",
    "data": "中文数据/案例翻译暂不可用；请查看英文证据字段。",
    "findings": "中文结果翻译暂不可用；请查看英文证据字段。",
    "limits": "中文局限翻译暂不可用；请查看英文证据字段。",
    "relevance": "中文相关性翻译暂不可用；请查看英文证据字段。",
}


def contains_cjk(text: str) -> bool:
    return any(0x4E00 <= ord(char) <= 0x9FFF for char in str(text or ""))


def fallback_zh(field: str) -> str:
    return FALLBACKS.get(field, "中文翻译暂不可用；请查看英文证据字段。")


def is_fallback(text: str) -> bool:
    return str(text or "").startswith("中文") and "暂不可用" in str(text or "")


def cache_key(text: str) -> str:
    return hashlib.sha256(str(text).encode("utf-8")).hexdigest()


def _join_google_segments(payload: Any) -> str:
    if not isinstance(payload, list) or not payload or not isinstance(payload[0], list):
        return ""
    return "".join(str(segment[0]) for segment in payload[0] if isinstance(segment, list) and segment and segment[0])


def google_translate(text: str, timeout: int = 30) -> str:
    source = str(text or "").strip()
    if not source:
        return ""
    # Google’s public endpoint is length-sensitive; split at sentence boundaries.
    chunks = []
    remaining = source
    while len(remaining) > 3800:
        cut = max(remaining.rfind(". ", 0, 3800), remaining.rfind("。", 0, 3800), remaining.rfind(" ", 0, 3800))
        cut = cut if cut > 200 else 3800
        chunks.append(remaining[:cut].strip())
        remaining = remaining[cut:].strip()
    if remaining:
        chunks.append(remaining)
    translated = []
    for chunk in chunks:
        query = urllib.parse.urlencode({"client": "gtx", "sl": "auto", "tl": "zh-CN", "dt": "t", "q": chunk})
        request = urllib.request.Request(
            "https://translate.googleapis.com/translate_a/single?" + query,
            headers={"User-Agent": "Codex zotero-literature-visualizer metadata translator"},
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
        result = _join_google_segments(payload)
        if not result:
            raise RuntimeError("translation endpoint returned an empty response")
        translated.append(result)
    return " ".join(translated).strip()


def retry_google_translate(text: str, attempts: int = 3) -> str:
    # //============XJQ(本次修改：对公开翻译接口限流/瞬时失败进行有限重试）====================//
    error = None
    for attempt in range(attempts):
        try:
            return google_translate(text)
        except Exception as exc:
            error = exc
            if attempt + 1 < attempts:
                time.sleep(0.8 * (attempt + 1))
    raise RuntimeError(str(error or "translation failed"))
    # //================XJQ(本次修改：对公开翻译接口限流/瞬时失败进行有限重试 END===============//


def _safe_translate(field: str, text: str, translator: Callable[[str], str]) -> str:
    source = str(text or "").strip()
    if not source:
        return fallback_zh(field)
    try:
        result = str(translator(source) or "").strip()
    except Exception:
        return fallback_zh(field)
    if not contains_cjk(result):
        return fallback_zh(field)
    if len(source) >= 80 and source in result:
        return fallback_zh(field)
    return result


def translate_bundle(fields: dict[str, str], translator: Callable[[str], str] | None = None) -> dict[str, str]:
    """Translate a field mapping; injected translators make this unit-testable."""
    if translator is not None:
        return {field: _safe_translate(field, fields.get(field, ""), translator) for field in fields}
    return translate_bundle_batched(fields)


def translate_bundle_batched(fields: dict[str, str], translator: Callable[[str], str] | None = None) -> dict[str, str]:
    """Translate all fields in one request, preserving ASCII field markers."""
    translator = translator or retry_google_translate
    active = {field: str(fields.get(field, "") or "").strip()[:650] for field in fields if str(fields.get(field, "") or "").strip()}
    if not active:
        return {field: fallback_zh(field) for field in fields}
    markers = {field: f"{MARKER_PREFIX}{index}X" for index, field in enumerate(active, start=1)}
    bundle = "\n".join(f"{markers[field]} {active[field]}" for field in active)
    try:
        translated = str(translator(bundle) or "")
    except Exception:
        return {field: _safe_translate(field, active[field], translator) for field in fields}
    if not contains_cjk(translated) or not all(marker in translated for marker in markers.values()):
        return {field: _safe_translate(field, active[field], translator) for field in fields}
    result = {}
    ordered = list(active)
    for index, field in enumerate(ordered):
        marker = markers[field]
        start = translated.find(marker) + len(marker)
        end = translated.find(markers[ordered[index + 1]], start) if index + 1 < len(ordered) else len(translated)
        # //============XJQ(本次修改：接受已完成的批量译文，避免把译文误判为原文而回退）====================//
        segment = translated[start:end].strip()
        result[field] = segment if contains_cjk(segment) else fallback_zh(field)
        # //================XJQ(本次修改：接受已完成的批量译文，避免把译文误判为原文而回退 END===============//
    return {field: result.get(field, fallback_zh(field)) for field in fields}


def load_cache(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {}
    except Exception:
        return {}


def save_cache(path: Path, cache: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")


def translate_spec(papers_path: Path, spec_path: Path, cache_path: Path, max_workers: int = 6, offline: bool = False) -> dict[str, int]:
    papers_payload = json.loads(papers_path.read_text(encoding="utf-8-sig"))
    spec = json.loads(spec_path.read_text(encoding="utf-8-sig"))
    papers = {str(paper.get("rank")): paper for paper in papers_payload.get("papers", [])}
    details = spec.get("details") if isinstance(spec.get("details"), dict) else {}
    cache = load_cache(cache_path)
    jobs = []
    for rank, detail in details.items():
        if not isinstance(detail, dict):
            continue
        fields = {field: str((detail.get(field) or {}).get("en") or "") for field in TRANSLATABLE_FIELDS}
        # //============XJQ(本次修改：把英文论文题目纳入主题翻译，避免 ZH 丢失标题信息）====================//
        paper = papers.get(rank, {})
        title = str(paper.get("title") or "").strip()
        if title and fields.get("topic"):
            fields["topic"] = f"Title: {title}. {fields['topic']}"
        # //================XJQ(本次修改：把英文论文题目纳入主题翻译，避免 ZH 丢失标题信息 END===============//
        missing = {field: value for field, value in fields.items() if value and (cache_key(value) not in cache or is_fallback(cache.get(cache_key(value), "")))}
        jobs.append((rank, fields, missing))

    def run_job(job: tuple[str, dict[str, str], dict[str, str]]) -> tuple[str, dict[str, str], dict[str, str]]:
        rank, fields, missing = job
        # //============XJQ(本次修改：复用缓存翻译，避免重复请求后遗漏写回 ZH）====================//
        translated = {field: cache[cache_key(value)] for field, value in fields.items() if value and cache_key(value) in cache and not is_fallback(cache.get(cache_key(value), ""))}
        if offline:
            return rank, {field: translated.get(field, fallback_zh(field)) for field in fields}, {}
        fresh = translate_bundle_batched(missing) if missing else {}
        translated.update(fresh)
        return rank, translated, {cache_key(fields[field]): fresh[field] for field in missing if field in fresh and not is_fallback(fresh[field])}
        # //================XJQ(本次修改：复用缓存翻译，避免重复请求后遗漏写回 ZH END===============//

    translated_count = 0
    fallback_count = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        for rank, translated, additions in executor.map(run_job, jobs):
            cache.update(additions)
            detail = details[rank]
            for field, source in (translated.items() if translated else []):
                if not source:
                    continue
                if not isinstance(detail.get(field), dict):
                    detail[field] = {}
                detail[field]["zh"] = source
                if source.startswith("中文") and "暂不可用" in source:
                    fallback_count += 1
                else:
                    translated_count += 1
    spec["details"] = details
    spec["zh_translation"] = {
        "status": "completed",
        "target_language": "zh-CN",
        "source_fields": "EN evidence fields",
        "policy": "ZH is translated from title/abstract/open metadata evidence; when translation fails, use a Chinese-only fallback and keep EN unchanged.",
        "cache_file": str(cache_path),
    }
    spec_path.write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")
    save_cache(cache_path, cache)
    return {"papers": len(papers), "details": len(details), "translated_fields": translated_count, "fallback_fields": fallback_count, "cache_entries": len(cache)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Translate dashboard EN evidence fields into Chinese.")
    parser.add_argument("--papers", required=True)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--cache", default="")
    parser.add_argument("--max-workers", type=int, default=6)
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args()
    papers_path = Path(args.papers)
    spec_path = Path(args.spec)
    cache = Path(args.cache) if args.cache else spec_path.parent / "metadata" / "zh-translation-cache.json"
    result = translate_spec(papers_path, spec_path, cache, max_workers=max(1, args.max_workers), offline=args.offline)
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# //================XJQ(本次修改：为 dashboard 提供真正中文的逐篇证据翻译和离线安全回退 END===============//
