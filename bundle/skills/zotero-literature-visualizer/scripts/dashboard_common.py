#!/usr/bin/env python3
"""Shared theme, styles, JS helpers, and templates for the dashboard renderers.

Both build_literature_dashboard.py (review layout) and large_library_dashboard.py
(large-library layout) interpolate SHARED_CSS / SHARED_JS into their HTML
templates so the two dashboards keep one visual language: an editorial
"warm paper" academic look, light/dark theme variables, a CVD-validated
categorical palette with per-mode steps, CJK-aware typography, tooltips,
filter chips, modal styling, citation export, reading-status + notes storage,
focus management, and URL hash state.

Everything stays dependency-free and offline: no CDN fonts, no external
scripts, output opens directly from disk.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


# Categorical palette (light-mode steps). The eight hues and their fixed order
# follow a colorblind-validated reference palette: adjacent-pair CVD deltaE
# passes in both modes, so donut neighbors and stacked hues stay tellable
# apart. Dark-mode steps live in CSS as --cat-1..8 overrides; the JS
# resolveColor() maps these hex values (and the legacy Tableau hexes from
# older dashboard-spec.json files) onto the CSS variables so charts adapt to
# the active theme without a rebuild.
PALETTE = [
    "#2a78d6",  # blue
    "#eb6834",  # orange
    "#1baf7a",  # aqua-green
    "#eda100",  # yellow
    "#e87ba4",  # magenta
    "#008300",  # green
    "#4a3aa7",  # violet
    "#e34948",  # red
]

# Older skill versions wrote these Tableau 10 hexes into dashboard-spec.json.
# resolveColor() folds them onto the new slots so regenerating the HTML around
# an old spec still picks up the refreshed look.
LEGACY_PALETTE = [
    "#4e79a7", "#f28e2b", "#59a14f", "#e15759", "#b07aa1",
    "#76b7b2", "#edc948", "#9c755f", "#ff9da7", "#86a873",
]


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_js(path: Path, var_name: str, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    body = json.dumps(payload, ensure_ascii=False, indent=2)
    path.write_text(f"window.{var_name} = {body};\n", encoding="utf-8")


def inline_js_tag(var_name: str, payload: Any) -> str:
    """Return a <script> tag that inlines the payload for single-file dashboards."""
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    body = body.replace("</", "<\\/")
    return f"<script>window.{var_name} = {body};</script>"


# Inline <script> that applies the saved theme before first paint (no flash).
THEME_BOOT_JS = r"""(function(){try{var m=localStorage.getItem('slr-theme');var d=window.matchMedia&&matchMedia('(prefers-color-scheme: dark)').matches;document.documentElement.dataset.theme=(m==='light'||m==='dark')?m:(d?'dark':'light');var l=localStorage.getItem('slr-lang');document.documentElement.dataset.lang=(l==='zh'||l==='en')?l:'both';}catch(e){}})();"""


SHARED_CSS = r"""
    :root {
      color-scheme: light;
      --bg:#f5f3ed; --panel:#fffefa; --panel-2:#f8f6ef;
      --ink:#221f18; --muted:#6f695c; --line:#e6e1d4; --line-strong:#d1c9b8;
      --accent:#2a78d6; --accent-soft:#e7effa; --link:#1c5cab; --focus:#3987e5;
      --ok:#0d7a52; --star:#d9930d; --reading:#b97708; --shell:rgba(28,23,13,.5);
      --chip-bg:#f2efe6; --chip-line:#d8d1c0; --track:#edeade; --track-line:#e0dbcb;
      --mark:#ffe9a3; --tip-bg:#fffefa;
      --tag-theme-ink:#17568c; --tag-theme-bg:#e9f1fb; --tag-theme-line:#cadcf0;
      --tag-method-ink:#0f6a4a; --tag-method-bg:#e6f4ec; --tag-method-line:#c4e3d2;
      --tag-if-ink:#8a5800; --tag-if-bg:#fcf2d5; --tag-if-line:#edd9a4;
      --tag-sub-ink:#7b5b1d; --tag-sub-bg:#f9f2da; --tag-sub-line:#e7d9b0;
      --btn-active-bg:#26221a; --btn-active-ink:#fffdf6;
      --cat-1:#2a78d6; --cat-2:#eb6834; --cat-3:#1baf7a; --cat-4:#eda100;
      --cat-5:#e87ba4; --cat-6:#008300; --cat-7:#4a3aa7; --cat-8:#e34948;
      --shadow:0 1px 2px rgba(64,52,28,.05), 0 14px 34px rgba(64,52,28,.07);
      --shadow-pop:0 24px 70px rgba(38,30,14,.28);
      --font-display:Georgia, "Iowan Old Style", "Times New Roman", "Songti SC",
        "Noto Serif CJK SC", "Source Han Serif SC", "SimSun", serif;
    }
    :root[data-theme="dark"] {
      color-scheme: dark;
      --bg:#141310; --panel:#1e1b16; --panel-2:#242019;
      --ink:#ece7db; --muted:#a19a8a; --line:#302c24; --line-strong:#474031;
      --accent:#3987e5; --accent-soft:#1a2a3f; --link:#85b5ee; --focus:#66a8e0;
      --ok:#3aa981; --star:#e8b93e; --reading:#d99a2b; --shell:rgba(0,0,0,.66);
      --chip-bg:#282419; --chip-line:#474031; --track:#262319; --track-line:#343026;
      --mark:#6b5a1c; --tip-bg:#262218;
      --tag-theme-ink:#93c4ec; --tag-theme-bg:#16293c; --tag-theme-line:#2c4e6e;
      --tag-method-ink:#8ed4b4; --tag-method-bg:#12312a; --tag-method-line:#275d4a;
      --tag-if-ink:#e6c579; --tag-if-bg:#33290f; --tag-if-line:#67542a;
      --tag-sub-ink:#e0ca90; --tag-sub-bg:#322a12; --tag-sub-line:#64562c;
      --btn-active-bg:#ece7db; --btn-active-ink:#17150e;
      --cat-1:#3987e5; --cat-2:#d95926; --cat-3:#199e70; --cat-4:#c98500;
      --cat-5:#d55181; --cat-6:#008300; --cat-7:#9085e9; --cat-8:#e66767;
      --shadow:0 1px 2px rgba(0,0,0,.4), 0 14px 34px rgba(0,0,0,.38);
      --shadow-pop:0 24px 70px rgba(0,0,0,.55);
    }
    * { box-sizing:border-box; }
    html { -webkit-text-size-adjust:100%; }
    body {
      margin:0; color:var(--ink);
      background:
        radial-gradient(1150px 430px at 78% -12%, var(--accent-soft), transparent 62%),
        radial-gradient(900px 380px at -10% -6%, var(--chip-bg), transparent 55%),
        var(--bg);
      font-family:-apple-system, "Segoe UI", "Segoe UI Variable Text", Roboto, "Helvetica Neue", Arial,
        "Microsoft YaHei", "PingFang SC", "Hiragino Sans GB", "Noto Sans SC", sans-serif;
      transition:background-color .25s ease, color .25s ease;
    }
    h1, h2, h3 { margin:0; letter-spacing:0; }
    h1, h2 { font-family:var(--font-display); font-weight:640; }
    p { margin:0; }
    a { color:var(--link); }
    button, input, select, textarea { font:inherit; color:var(--ink); }
    button {
      appearance:none; border:1px solid var(--line); background:var(--panel); border-radius:9px;
      min-height:34px; padding:7px 12px; cursor:pointer;
      transition:border-color .15s ease, background-color .15s ease, color .15s ease;
    }
    button:hover { border-color:var(--line-strong); background:var(--panel-2); }
    button[aria-pressed="true"] { background:var(--btn-active-bg); color:var(--btn-active-ink); border-color:var(--btn-active-bg); }
    button.ghost { background:transparent; }
    input, select {
      min-height:38px; border:1px solid var(--line); border-radius:10px; background:var(--panel);
      padding:8px 12px; width:100%;
    }
    input::placeholder { color:var(--muted); }
    :focus-visible { outline:2px solid var(--focus); outline-offset:2px; }
    mark { background:var(--mark); color:inherit; border-radius:3px; padding:0 1px; }
    html[data-lang="zh"] .le, html[data-lang="zh"] .sep, html[data-lang="zh"] .lang-label { display:none; }
    html[data-lang="en"] .lz, html[data-lang="en"] .sep, html[data-lang="en"] .lang-label { display:none; }

    .panel, .kpi, .card, .detail-card { background:var(--panel); border:1px solid var(--line); border-radius:14px; box-shadow:var(--shadow); }
    .hint, .small { color:var(--muted); font-size:12px; line-height:1.5; }
    .brandline { height:3px; border-radius:999px; flex:0 0 auto;
      background:linear-gradient(90deg, var(--cat-1), var(--cat-3) 30%, var(--cat-4) 55%, var(--cat-2) 78%, var(--cat-5)); }
    .eyebrow-label { color:var(--muted); font-size:11px; letter-spacing:.14em; text-transform:uppercase; font-weight:650; }
    .toolbar { display:flex; gap:7px; flex-wrap:wrap; justify-content:flex-end; align-items:center; }
    .toolbar .ghost { min-width:44px; }
    .searchbar { position:relative; margin-top:14px; }
    .searchbar input { padding-left:36px; font-size:14.5px; min-height:42px; }
    .searchbar::before { content:"⌕"; position:absolute; left:12px; top:50%; transform:translateY(-56%); color:var(--muted); font-size:20px; pointer-events:none; }
    .searchbar .slash-hint { position:absolute; right:11px; top:50%; transform:translateY(-50%); border:1px solid var(--line); color:var(--muted);
      border-radius:6px; font-size:11px; padding:2px 7px; pointer-events:none; background:var(--panel-2); }

    .kpis { display:grid; gap:10px; }
    .kpi { padding:14px 15px; min-height:92px; }
    .kpi .label { color:var(--muted); font-size:10.5px; text-transform:uppercase; letter-spacing:.12em; font-weight:650; }
    .kpi .value { margin-top:7px; font-size:31px; line-height:1; font-variant-numeric:tabular-nums;
      font-family:var(--font-display); font-weight:640; }
    .kpi .note { margin-top:8px; color:var(--muted); font-size:11px; line-height:1.35; }
    .kpi[role="button"] { cursor:pointer; transition:border-color .15s ease, transform .15s ease; }
    .kpi[role="button"]:hover { border-color:var(--line-strong); transform:translateY(-1px); }
    .kpi[aria-pressed="true"] { border-color:var(--accent); box-shadow:inset 0 0 0 1px var(--accent), var(--shadow); }

    .readbar { margin-top:13px; }
    .readbar-top { display:flex; justify-content:space-between; align-items:baseline; gap:10px; color:var(--muted); font-size:11.5px; }
    .readbar-top b { color:var(--ink); font-variant-numeric:tabular-nums; font-weight:700; }
    .readbar .track { position:relative; height:8px; margin-top:6px; }
    .readbar .fill { position:absolute; inset:0 auto 0 0; border-radius:999px; min-width:0; transition:width .5s cubic-bezier(.25,.7,.3,1); }
    .readbar .fill.rg { background:var(--reading); opacity:.38; }
    .readbar .fill.rd { background:var(--ok); }

    .chipbar { display:flex; flex-wrap:wrap; gap:8px; margin:0 0 12px; align-items:center; }
    .chipbar[hidden] { display:none; }
    .fchip {
      display:inline-flex; align-items:center; gap:7px; min-height:30px;
      border:1px solid var(--chip-line); background:var(--chip-bg); border-radius:999px;
      padding:4px 12px; font-size:12px; line-height:1.2;
    }
    .fchip .x { color:var(--muted); font-size:14px; line-height:1; }
    .fchip:hover { border-color:var(--accent); background:var(--chip-bg); }
    .fchip:hover .x { color:var(--accent); }
    .fchip.clear { background:transparent; border-style:dashed; color:var(--muted); }

    .tags { display:flex; gap:6px; flex-wrap:wrap; }
    .tag { border-radius:999px; padding:4px 9px; font-size:11.5px; line-height:1.1; border:1px solid var(--line); color:var(--muted); background:var(--panel);
      white-space:nowrap; display:inline-block; max-width:100%; overflow:hidden; text-overflow:ellipsis; }
    .tag.theme { color:var(--tag-theme-ink); background:var(--tag-theme-bg); border-color:var(--tag-theme-line); }
    .tag.method { color:var(--tag-method-ink); background:var(--tag-method-bg); border-color:var(--tag-method-line); }
    .tag.if { color:var(--tag-if-ink); background:var(--tag-if-bg); border-color:var(--tag-if-line); font-variant-numeric:tabular-nums; }
    .tag.subtheme { color:var(--tag-sub-ink); background:var(--tag-sub-bg); border-color:var(--tag-sub-line); }
    .tag.pdf { color:var(--ok); border-color:currentColor; background:transparent; font-weight:650; }
    .tag.new { color:#b3384d; background:#fdeaee; border-color:#f3c9d2; font-weight:750; letter-spacing:.05em; }
    :root[data-theme="dark"] .tag.new { color:#f2a0af; background:#3d1922; border-color:#6e2c3a; }
    .tag.cas { font-weight:680; }
    .tag.cas1 { color:#9e2b25; background:#fbe9e7; border-color:#eec7c3; }
    .tag.cas2 { color:#9a5a10; background:#fcf1de; border-color:#eed6ab; }
    .tag.cas3 { color:#1f5d92; background:#e9f2fb; border-color:#c9def1; }
    .tag.cas4 { color:#6b665a; background:#f2efe7; border-color:#d9d2c2; }
    :root[data-theme="dark"] .tag.cas1 { color:#f09d97; background:#3a1a17; border-color:#6b3029; }
    :root[data-theme="dark"] .tag.cas2 { color:#e5b877; background:#33270f; border-color:#66512a; }
    :root[data-theme="dark"] .tag.cas3 { color:#8fc0e8; background:#152a3c; border-color:#2b4d6e; }
    :root[data-theme="dark"] .tag.cas4 { color:#a59e8e; background:#282419; border-color:#474031; }
    .tag.cited { color:var(--tag-theme-ink); background:transparent; border-color:var(--tag-theme-line); font-variant-numeric:tabular-nums; }

    .rstat { display:inline-flex; align-items:center; gap:6px; min-height:26px; padding:3px 10px; border-radius:999px;
      font-size:11.5px; color:var(--muted); background:var(--panel); border:1px solid var(--line); }
    .rstat .d { width:7px; height:7px; border-radius:999px; background:var(--line-strong); flex:0 0 auto; }
    .rstat:hover { border-color:var(--line-strong); }
    .rstat[data-s="reading"] { color:var(--tag-sub-ink); background:var(--tag-sub-bg); border-color:var(--tag-sub-line); }
    .rstat[data-s="reading"] .d { background:var(--reading); }
    .rstat[data-s="read"] { color:var(--tag-method-ink); background:var(--tag-method-bg); border-color:var(--tag-method-line); }
    .rstat[data-s="read"] .d { background:var(--ok); }
    .star-btn { border:0; background:transparent; min-height:26px; padding:2px 5px; font-size:16px; line-height:1;
      color:var(--line-strong); border-radius:7px; }
    .star-btn:hover { color:var(--star); background:transparent; border:0; }
    .star-btn[aria-pressed="true"] { color:var(--star); background:transparent; border:0; }

    .notes-block .notes-row { display:flex; gap:8px; align-items:center; flex-wrap:wrap; margin:9px 0; }
    .notes-block .seg-note { display:inline-flex; border:1px solid var(--line); border-radius:9px; overflow:hidden; }
    .notes-block .seg-note button { border:0; border-radius:0; min-height:31px; font-size:12.5px; background:transparent; padding:5px 12px; }
    .notes-block .seg-note button + button { border-left:1px solid var(--line); }
    .notes-block .seg-note button[aria-pressed="true"] { background:var(--btn-active-bg); color:var(--btn-active-ink); }
    .note-area { width:100%; min-height:86px; resize:vertical; border:1px solid var(--line); border-radius:10px;
      background:var(--panel-2); padding:10px 12px; font-size:13.5px; line-height:1.6; }
    .note-area::placeholder { color:var(--muted); }
    .notes-hint { color:var(--muted); font-size:11px; font-weight:400; letter-spacing:0; text-transform:none; }

    .bars { display:grid; gap:11px; }
    .bar { display:grid; grid-template-columns:minmax(170px,250px) 1fr 46px; gap:12px; align-items:center; border-radius:9px; }
    .bar[role="button"] { cursor:pointer; padding:4px 6px; margin:-4px -6px; }
    .bar[role="button"]:hover { background:var(--panel-2); }
    .bar[aria-pressed="true"] { background:var(--chip-bg); }
    .bar-name { min-width:0; font-size:13px; font-weight:650; line-height:1.3; }
    .bar-name .sub { display:block; color:var(--muted); font-size:11px; font-weight:500; margin-top:3px; }
    .track { height:13px; border:1px solid var(--track-line); background:var(--track); border-radius:999px; overflow:hidden; }
    .fill { height:100%; min-width:6px; border-radius:999px; background:var(--accent); transition:width .55s cubic-bezier(.25,.7,.3,1); }
    .count { color:var(--muted); text-align:right; font-size:13px; font-variant-numeric:tabular-nums; }

    .tl { display:flex; align-items:stretch; gap:6px; }
    .tl-col { flex:1; min-width:0; display:grid; grid-template-rows:1fr auto auto; gap:5px; border:0; background:transparent; padding:0; border-radius:6px; cursor:pointer; }
    .tl-bar { height:96px; display:flex; align-items:flex-end; border-radius:7px; background:var(--track); border:1px solid var(--track-line); overflow:hidden; }
    .tl-fill { width:100%; background:var(--accent); opacity:.55; border-radius:4px 4px 0 0; transition:height .5s cubic-bezier(.25,.7,.3,1), opacity .15s ease; }
    .tl-col:hover .tl-fill { opacity:.85; }
    .tl-col[aria-pressed="true"] .tl-fill { opacity:1; }
    .tl-col[aria-pressed="true"] .tl-lab { color:var(--ink); font-weight:700; }
    .tl-n { text-align:center; font-size:11px; color:var(--muted); font-variant-numeric:tabular-nums; }
    .tl-lab { text-align:center; font-size:11px; color:var(--muted); white-space:nowrap; }

    .slr-tip {
      position:fixed; left:0; top:0; z-index:80; max-width:340px;
      background:var(--tip-bg); color:var(--ink); border:1px solid var(--line-strong); border-radius:10px;
      padding:9px 11px; font-size:12px; line-height:1.5; pointer-events:none;
      opacity:0; transform:translateY(3px); transition:opacity .12s ease, transform .12s ease;
      box-shadow:var(--shadow-pop);
    }
    .slr-tip.show { opacity:1; transform:none; }
    .slr-tip b { font-weight:700; }
    .slr-tip .tip-sub { color:var(--muted); display:block; margin-top:3px; }

    .detail-shell { position:fixed; inset:0; display:none; background:var(--shell); z-index:50; padding:22px; overflow:auto;
      backdrop-filter:blur(5px); -webkit-backdrop-filter:blur(5px); }
    .detail-shell.open { display:block; }
    .detail-card { width:min(940px, calc(100vw - 32px)); margin:0 auto; padding:24px 26px; box-shadow:var(--shadow-pop);
      border-top:4px solid var(--dc, var(--accent)); animation:slrCardIn .22s ease; }
    @keyframes slrCardIn { from { opacity:0; transform:translateY(12px) scale(.985); } to { opacity:1; transform:none; } }
    .detail-top { display:flex; justify-content:space-between; gap:12px; align-items:flex-start; margin-bottom:10px; }
    .eyebrow { color:var(--muted); font-size:12px; margin-bottom:7px; }
    .detail-card h2 { font-size:24px; line-height:1.3; }
    .detail-actions { display:flex; gap:7px; flex:0 0 auto; align-items:center; }
    .icon-button { width:36px; min-height:36px; padding:0; display:grid; place-items:center; font-size:18px; }
    .icon-button:disabled { opacity:.4; cursor:default; }
    .detail-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:9px; margin:14px 0; }
    .detail-fact { border:1px solid var(--line); border-radius:10px; padding:9px 11px; background:var(--panel-2); }
    .detail-fact span { display:block; color:var(--muted); font-size:11px; margin-bottom:4px; }
    .detail-fact strong { font-size:13px; line-height:1.3; overflow-wrap:anywhere; }
    .detail-section { border-top:1px solid var(--line); padding-top:12px; margin-top:12px; }
    .detail-section h3 { font-size:14.5px; margin-bottom:7px; }
    .detail-section p { margin:6px 0; font-size:14px; line-height:1.65; }
    .lang-label { display:inline-block; min-width:26px; color:var(--muted); font-size:12px; font-weight:700; margin-right:4px; }
    .placeholder-note { color:var(--muted); font-style:italic; }
    .detail-links { display:flex; flex-wrap:wrap; gap:8px; margin-top:15px; }
    .detail-link { display:inline-flex; align-items:center; gap:6px; min-height:34px; border:1px solid var(--line); border-radius:9px; padding:7px 12px; background:var(--panel); color:var(--link); text-decoration:none; cursor:pointer; font-size:13px; }
    .detail-link:hover { border-color:var(--line-strong); background:var(--panel-2); }

    @media (prefers-reduced-motion: reduce) {
      *, *::before, *::after { transition:none !important; animation:none !important; }
    }
    @media print {
      body { background:#fff; }
      .toolbar, .searchbar, .chipbar, .tabs, .controls, .results-actions, .detail-shell, .slr-tip,
      .rstat, .star-btn, .readbar { display:none !important; }
      .panel, .card, .kpi { box-shadow:none; break-inside:avoid; }
    }
"""


SHARED_JS = r"""
window.SLR = (function () {
  const reduced = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;
  function escapeHtml(value) {
    return String(value == null ? "" : value).replace(/[&<>"']/g, ch => ({ "&":"&amp;", "<":"&lt;", ">":"&gt;", "\"":"&quot;", "'":"&#39;" }[ch]));
  }
  function B(zh, en) {
    if (!en || zh === en) return escapeHtml(zh);
    if (!zh) return escapeHtml(en);
    return `<span class="lz">${escapeHtml(zh)}</span><span class="sep"> / </span><span class="le">${escapeHtml(en)}</span>`;
  }
  // Map palette hexes (new + legacy Tableau) onto theme-reactive CSS variables
  // so every chart recolors itself when the light/dark toggle flips.
  const CAT_LIGHT = ["#2a78d6","#eb6834","#1baf7a","#eda100","#e87ba4","#008300","#4a3aa7","#e34948"];
  const CAT_LEGACY = ["#4e79a7","#f28e2b","#59a14f","#e15759","#b07aa1","#76b7b2","#edc948","#9c755f","#ff9da7","#86a873"];
  const CAT_VARS = (function () {
    const map = {};
    CAT_LIGHT.forEach((hex, i) => { map[hex] = `var(--cat-${i + 1})`; });
    CAT_LEGACY.forEach((hex, i) => { if (!map[hex]) map[hex] = `var(--cat-${(i % 8) + 1})`; });
    return map;
  })();
  function resolveColor(hex) {
    const key = String(hex || "").toLowerCase();
    return CAT_VARS[key] || hex || "var(--cat-1)";
  }
  // Same mapping, but always resolving to a concrete light-mode hex — needed by
  // the canvas share card, which cannot read CSS variables.
  function resolveHexLight(color) {
    const key = String(color || "").toLowerCase();
    if (CAT_LIGHT.includes(key)) return key;
    const legacy = CAT_LEGACY.indexOf(key);
    if (legacy >= 0) return CAT_LIGHT[legacy % 8];
    const varMatch = key.match(/var\(--cat-(\d)\)/);
    if (varMatch) return CAT_LIGHT[Number(varMatch[1]) - 1] || CAT_LIGHT[0];
    return /^#([0-9a-f]{3}|[0-9a-f]{6})$/.test(key) ? key : CAT_LIGHT[0];
  }
  function casTier(p) {
    const m = String(p.cas_partition || "").match(/[1-4]/);
    return m ? m[0] : "";
  }
  function casTagHtml(p) {
    const tier = casTier(p);
    if (!tier) return "";
    const top = p.cas_top ? " Top" : "";
    return `<span class="tag cas cas${tier}">中科院${tier}区${top}</span>`;
  }
  function casLabel(p) {
    const tier = casTier(p);
    return tier ? `中科院${tier}区${p.cas_top ? " Top" : ""}` : "";
  }
  function fileUrl(path) { return path ? encodeURI("file:///" + String(path).replace(/\\/g, "/")) : ""; }
  function yearOf(p) {
    const fields = [p.publication_year, p.year, p.published_year, p.publication_date, p.published_date, p.date];
    for (const v of fields) { const m = String(v || "").match(/(?:19|20)\d{2}/); if (m) return m[0]; }
    return "";
  }
  function monthOf(p) {
    const m = String(p.publication_date || "").match(/((?:19|20)\d{2})[-/.](\d{1,2})/);
    return m ? m[1] + "-" + String(m[2]).padStart(2, "0") : "";
  }
  function initTheme(btn) {
    const KEY = "slr-theme";
    const mq = matchMedia("(prefers-color-scheme: dark)");
    let mode = localStorage.getItem(KEY);
    if (mode !== "light" && mode !== "dark") mode = "auto";
    function apply() {
      document.documentElement.dataset.theme = mode === "auto" ? (mq.matches ? "dark" : "light") : mode;
      if (btn) {
        btn.textContent = mode === "auto" ? "◐" : (mode === "light" ? "☀" : "☾");
        btn.title = "外观 / Theme: " + (mode === "auto" ? "auto" : mode);
      }
    }
    mq.addEventListener("change", apply);
    if (btn) btn.addEventListener("click", () => {
      mode = mode === "auto" ? "light" : (mode === "light" ? "dark" : "auto");
      try { localStorage.setItem(KEY, mode === "auto" ? "" : mode); } catch (e) {}
      apply();
    });
    apply();
  }
  function initLang(btn) {
    const KEY = "slr-lang";
    const modes = ["both", "zh", "en"];
    let mode = localStorage.getItem(KEY);
    if (!modes.includes(mode)) mode = "both";
    function apply() {
      document.documentElement.dataset.lang = mode;
      if (btn) { btn.textContent = mode === "both" ? "双语" : (mode === "zh" ? "中文" : "EN"); btn.title = "语言 / Language"; }
    }
    if (btn) btn.addEventListener("click", () => {
      mode = modes[(modes.indexOf(mode) + 1) % modes.length];
      try { localStorage.setItem(KEY, mode); } catch (e) {}
      apply();
    });
    apply();
  }
  function bindSlashFocus(input) {
    if (!input) return;
    document.addEventListener("keydown", e => {
      if (e.key !== "/" || e.ctrlKey || e.metaKey || e.altKey) return;
      const tag = (e.target.tagName || "").toLowerCase();
      if (tag === "input" || tag === "textarea" || tag === "select") return;
      e.preventDefault();
      input.focus();
      input.select();
    });
  }

  // ---- Reading status / star / personal notes (localStorage, per browser) ----
  const READ_STATES = ["", "reading", "read"];
  const READ_META = {
    "":       { zh: "未读", en: "Unread" },
    reading:  { zh: "在读", en: "Reading" },
    read:     { zh: "已读", en: "Read" },
  };
  function initNotes(storageKey) {
    let data = {};
    try { data = JSON.parse(localStorage.getItem(storageKey) || "{}") || {}; } catch (e) { data = {}; }
    function save() { try { localStorage.setItem(storageKey, JSON.stringify(data)); } catch (e) {} }
    return {
      key: storageKey,
      get(rank) { return data[String(rank)] || {}; },
      set(rank, patch) {
        const k = String(rank);
        data[k] = Object.assign({}, data[k], patch);
        if (!data[k].s && !data[k].star && !String(data[k].note || "").trim()) delete data[k];
        save();
      },
      cycle(rank) {
        const cur = (data[String(rank)] || {}).s || "";
        const next = READ_STATES[(READ_STATES.indexOf(cur) + 1) % READ_STATES.length];
        this.set(rank, { s: next });
        return next;
      },
      counts(list) {
        let read = 0, reading = 0, star = 0;
        list.forEach(p => {
          const e = this.get(p.rank);
          if (e.s === "read") read += 1; else if (e.s === "reading") reading += 1;
          if (e.star) star += 1;
        });
        return { read, reading, star };
      },
      matches(rank, filter) {
        const e = this.get(rank);
        if (!filter) return true;
        if (filter === "starred") return !!e.star;
        if (filter === "unread") return !(e.s === "read" || e.s === "reading");
        return (e.s || "") === filter;
      },
    };
  }
  function statusChipHtml(rank, entry, extraClass) {
    const s = entry.s || "";
    const meta = READ_META[s] || READ_META[""];
    return `<button class="rstat ${extraClass || ""}" type="button" data-read-rank="${escapeHtml(rank)}" data-s="${s}"
      title="点击切换 未读→在读→已读 / Click to cycle reading status"><i class="d"></i>${B(meta.zh, meta.en)}</button>`;
  }
  function starBtnHtml(rank, entry, extraClass) {
    const on = !!entry.star;
    return `<button class="star-btn ${extraClass || ""}" type="button" data-star-rank="${escapeHtml(rank)}"
      aria-pressed="${on}" title="星标 / Star">${on ? "★" : "☆"}</button>`;
  }
  function notesPanelHtml(rank, entry) {
    const s = entry.s || "";
    return `<section class="detail-section notes-block">
      <h3>${B("我的笔记", "My Notes")} <span class="notes-hint">${B("仅保存在本机浏览器", "stored locally in this browser")}</span></h3>
      <div class="notes-row">
        <span class="seg-note" role="group" aria-label="Reading status">
          ${READ_STATES.map(st => `<button type="button" data-note-status="${st}" aria-pressed="${st === s}">${B(READ_META[st].zh, READ_META[st].en)}</button>`).join("")}
        </span>
        ${starBtnHtml(rank, entry, "lg")}
      </div>
      <textarea class="note-area" data-note-rank="${escapeHtml(rank)}"
        placeholder="写点想法：创新点、可借鉴的方法、与我课题的关联… / Jot ideas: novelty, reusable methods, links to my own work…">${escapeHtml(entry.note || "")}</textarea>
    </section>`;
  }
  function bindNotesPanel(root, rank, notes, onChange) {
    root.querySelectorAll("[data-note-status]").forEach(btn => btn.addEventListener("click", () => {
      const cur = notes.get(rank).s || "";
      const next = btn.dataset.noteStatus === cur ? "" : btn.dataset.noteStatus;
      notes.set(rank, { s: next });
      root.querySelectorAll("[data-note-status]").forEach(b => b.setAttribute("aria-pressed", b.dataset.noteStatus === next));
      onChange();
    }));
    const star = root.querySelector("[data-star-rank]");
    if (star) star.addEventListener("click", () => {
      const on = !notes.get(rank).star;
      notes.set(rank, { star: on });
      star.setAttribute("aria-pressed", on);
      star.textContent = on ? "★" : "☆";
      onChange();
    });
    const area = root.querySelector("[data-note-rank]");
    if (area) area.addEventListener("input", debounce(() => { notes.set(rank, { note: area.value }); onChange(true); }, 350));
  }
  function renderReadbar(el, papers, notes) {
    if (!el) return;
    const c = notes.counts(papers);
    const total = papers.length || 1;
    el.innerHTML = `<div class="readbar-top">
        <span>${B("阅读进度", "Reading progress")}${c.star ? ` · <span style="color:var(--star)">★ ${c.star}</span>` : ""}</span>
        <b>${c.read}<span style="color:var(--muted);font-weight:500"> / ${papers.length}</span></b>
      </div>
      <div class="track">
        <span class="fill rg" style="width:${Math.round((c.read + c.reading) / total * 100)}%"></span>
        <span class="fill rd" style="width:${Math.round(c.read / total * 100)}%"></span>
      </div>`;
  }

  let tipEl = null;
  function tipNode() {
    if (!tipEl) { tipEl = document.createElement("div"); tipEl.className = "slr-tip"; document.body.appendChild(tipEl); }
    return tipEl;
  }
  function moveTip(x, y) {
    const el = tipNode();
    const r = el.getBoundingClientRect();
    let left = x + 14, top = y + 16;
    if (left + r.width > innerWidth - 8) left = Math.max(8, x - r.width - 12);
    if (top + r.height > innerHeight - 8) top = Math.max(8, y - r.height - 12);
    el.style.left = left + "px"; el.style.top = top + "px";
  }
  function showTip(html, x, y) { const el = tipNode(); el.innerHTML = html; el.classList.add("show"); moveTip(x, y); }
  function hideTip() { if (tipEl) tipEl.classList.remove("show"); }
  function bindTip(el, htmlFn) {
    el.addEventListener("mouseenter", e => showTip(htmlFn(), e.clientX, e.clientY));
    el.addEventListener("mousemove", e => moveTip(e.clientX, e.clientY));
    el.addEventListener("mouseleave", hideTip);
  }
  function countUp(el, target, dur) {
    target = Number(target) || 0;
    if (reduced || target <= 0) { el.textContent = String(target); return; }
    const t0 = performance.now(); dur = dur || 650;
    (function step(t) {
      const k = Math.min(1, (t - t0) / dur);
      el.textContent = String(Math.round(target * (1 - Math.pow(1 - k, 3))));
      if (k < 1) requestAnimationFrame(step);
    })(t0);
  }
  function debounce(fn, ms) { let id; return function (...a) { clearTimeout(id); id = setTimeout(() => fn.apply(this, a), ms); }; }
  function isPlaceholder(v) {
    const t = String(v || "").trim();
    return !t || t.startsWith("待补充") || t.startsWith("Add a concise evidence-grounded note");
  }
  function detailValueHtml(value) {
    if (value && typeof value === "object") {
      const zh = isPlaceholder(value.zh) ? "" : value.zh;
      const en = isPlaceholder(value.en) ? "" : value.en;
      if (!zh && !en) return `<p class="placeholder-note">${B("暂无总结，可在 dashboard-spec.json 补充", "Not summarized yet; refine dashboard-spec.json to fill this in")}</p>`;
      let out = "";
      out += zh ? `<p class="lz"><span class="lang-label">中</span>${escapeHtml(zh)}</p>` : `<p class="lz placeholder-note">暂无中文总结</p>`;
      out += en ? `<p class="le"><span class="lang-label">EN</span>${escapeHtml(en)}</p>` : `<p class="le placeholder-note">No English summary yet</p>`;
      return out;
    }
    if (isPlaceholder(value)) return `<p class="placeholder-note">${B("暂无总结", "Not summarized yet")}</p>`;
    return `<p>${escapeHtml(value)}</p>`;
  }
  function detailSection(titleHtml, value) {
    return `<section class="detail-section"><h3>${titleHtml}</h3>${detailValueHtml(value)}</section>`;
  }
  function splitAuthors(s) { return String(s || "").split(/\s*[;；]\s*/).map(x => x.trim()).filter(Boolean); }
  function apa(p) {
    const names = splitAuthors(p.authors).join(", ");
    const y = yearOf(p) || "n.d.";
    const bits = [];
    if (names) bits.push(names);
    bits.push(`(${y}).`);
    if (p.title) bits.push(String(p.title).replace(/\.?\s*$/, "."));
    if (p.journal) bits.push(String(p.journal) + ".");
    if (p.doi) bits.push(String(p.doi));
    return bits.join(" ");
  }
  function bibtex(p) {
    const strip = s => String(s || "").replace(/[{}\\]/g, "");
    const authors = splitAuthors(p.authors);
    const surname = (authors[0] || "ref").split(/\s+/)[0].replace(/[^A-Za-z一-鿿]/g, "") || "ref";
    const word = (String(p.title || "").match(/[A-Za-z]{3,}/) || ["paper"])[0].toLowerCase();
    const doi = String(p.doi || "").replace(/^https?:\/\/doi\.org\//, "");
    const rows = [];
    if (p.title) rows.push(["title", strip(p.title)]);
    if (authors.length) rows.push(["author", authors.map(strip).join(" and ")]);
    if (p.journal) rows.push(["journal", strip(p.journal)]);
    if (yearOf(p)) rows.push(["year", yearOf(p)]);
    if (doi) rows.push(["doi", doi]);
    if (p.doi) rows.push(["url", p.doi]);
    return `@article{${surname}${yearOf(p) || ""}${word},\n` + rows.map(([k, v]) => `  ${k} = {${v}}`).join(",\n") + "\n}";
  }
  function csv(list, columns) {
    const q = v => '"' + String(v == null ? "" : v).replace(/"/g, '""') + '"';
    const head = columns.map(c => q(c[0])).join(",");
    const rows = list.map(p => columns.map(c => q(c[1](p))).join(","));
    return "\\uFEFF" + [head].concat(rows).join("\r\n");
  }
  function download(name, text, mime) {
    downloadBlob(name, new Blob([text], { type: mime || "text/plain;charset=utf-8" }));
  }
  function downloadBlob(name, blob) {
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = name;
    document.body.appendChild(a);
    a.click();
    setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 400);
  }

  // ---- Zotero write-back package (consumed by zotero_api_import.py write-back) ----
  function exportWriteback(cfg) {
    const entries = cfg.papers.map(p => {
      const e = cfg.notes.get(p.rank);
      return {
        rank: p.rank, doi: p.doi || "", title: p.title || "", journal: p.journal || "",
        theme: cfg.themeOf(p), subtheme: cfg.subthemeOf ? cfg.subthemeOf(p) : "", method: cfg.methodOf(p),
        read_status: e.s || "", starred: !!e.star, note: e.note || "",
      };
    });
    download("zotero-writeback.json", JSON.stringify({
      generated_at: new Date().toISOString(),
      dashboard_title: cfg.title || "",
      entries,
    }, null, 2), "application/json;charset=utf-8");
  }

  // ---- Share card (vertical 1080x1440 poster drawn on canvas, light palette) ----
  const CARD = {
    bg: "#f6f4ee", panel: "#fffefa", ink: "#221f18", muted: "#6f695c", faint: "#8f887a",
    line: "#e6e1d4", track: "#edeade", ok: "#0d7a52", star: "#d9930d", newInk: "#b3384d", newBg: "#fdeaee",
    ifInk: "#8a5800", ifBg: "#fcf2d5", cas1Ink: "#9e2b25", cas1Bg: "#fbe9e7",
    serif: "Georgia, 'Songti SC', 'Noto Serif CJK SC', 'SimSun', serif",
    sans: "-apple-system, 'Segoe UI', Roboto, 'Microsoft YaHei', 'PingFang SC', sans-serif",
    footer: "Zotero Literature Visualizer · github.com/xuezheng627/zotero-literature-visualizer",
  };
  function rr(ctx, x, y, w, h, r) {
    if (ctx.roundRect) { ctx.beginPath(); ctx.roundRect(x, y, w, h, r); return; }
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.arcTo(x + w, y, x + w, y + h, r);
    ctx.arcTo(x + w, y + h, x, y + h, r);
    ctx.arcTo(x, y + h, x, y, r);
    ctx.arcTo(x, y, x + w, y, r);
    ctx.closePath();
  }
  function fitText(ctx, text, maxW) {
    let t = String(text == null ? "" : text);
    if (ctx.measureText(t).width <= maxW) return t;
    while (t.length && ctx.measureText(t + "…").width > maxW) t = t.slice(0, -1);
    return t + "…";
  }
  function wrapText(ctx, text, maxW, maxLines) {
    // CJK wraps per character; Latin wraps per word.
    const tokens = String(text || "").match(/[一-鿿]|[^一-鿿\s]+\s*|\s+/g) || [];
    const lines = [];
    let cur = "";
    let overflow = "";
    for (let i = 0; i < tokens.length; i += 1) {
      const tok = tokens[i];
      if (!cur || ctx.measureText(cur + tok).width <= maxW) {
        cur += tok;
        continue;
      }
      lines.push(cur.trimEnd());
      cur = tok.trimStart();
      if (lines.length === maxLines) { overflow = cur + tokens.slice(i + 1).join(""); cur = ""; break; }
    }
    if (lines.length < maxLines && cur.trimEnd()) lines.push(cur.trimEnd());
    else if (lines.length === maxLines && overflow.trim()) {
      lines[maxLines - 1] = fitText(ctx, lines[maxLines - 1] + " " + overflow.trim(), maxW);
    }
    return lines;
  }
  function cardPill(ctx, x, yMid, text, ink, bg, font) {
    ctx.font = font;
    const w = ctx.measureText(text).width + 30;
    const h = 42;
    ctx.fillStyle = bg;
    rr(ctx, x, yMid - h / 2, w, h, h / 2);
    ctx.fill();
    ctx.fillStyle = ink;
    ctx.textBaseline = "middle";
    ctx.fillText(text, x + 15, yMid + 2);
    return w;
  }
  function buildShareCardCanvas(cfg) {
    const W = 1080, H = 1440, M = 84, RIGHT = W - M;
    const canvas = document.createElement("canvas");
    canvas.width = W; canvas.height = H;
    const ctx = canvas.getContext("2d");
    ctx.textBaseline = "alphabetic";
    ctx.fillStyle = CARD.bg;
    ctx.fillRect(0, 0, W, H);
    ctx.fillStyle = CARD.panel;
    rr(ctx, 36, 36, W - 72, H - 72, 26);
    ctx.fill();
    ctx.strokeStyle = CARD.line;
    ctx.lineWidth = 2;
    rr(ctx, 36, 36, W - 72, H - 72, 26);
    ctx.stroke();

    const grad = ctx.createLinearGradient(M, 0, RIGHT, 0);
    [CAT_LIGHT[0], CAT_LIGHT[2], CAT_LIGHT[3], CAT_LIGHT[1], CAT_LIGHT[4]].forEach((hex, i, arr) =>
      grad.addColorStop(i / (arr.length - 1), hex));
    ctx.fillStyle = grad;
    rr(ctx, M, 92, W - 2 * M, 8, 4);
    ctx.fill();

    ctx.fillStyle = CARD.muted;
    ctx.font = `650 25px ${CARD.sans}`;
    try { ctx.letterSpacing = "4px"; } catch (e) {}
    ctx.fillText("我的文献库 · LITERATURE LIBRARY", M, 158);
    try { ctx.letterSpacing = "0px"; } catch (e) {}

    ctx.fillStyle = CARD.ink;
    ctx.font = `700 56px ${CARD.serif}`;
    const titleLines = wrapText(ctx, cfg.title || "Literature Review", W - 2 * M, 2);
    let y = 224;
    titleLines.forEach(line => { ctx.fillText(line, M, y); y += 72; });
    y -= 72;

    ctx.fillStyle = CARD.muted;
    ctx.font = `400 26px ${CARD.sans}`;
    const dateStr = cfg.dateStr || new Date().toISOString().slice(0, 10);
    ctx.fillText(`${dateStr} 生成 · 共 ${cfg.papers} 篇文献`, M, y + 52);

    const statY = y + 175;
    const stats = [
      [String(cfg.papers), "文献 PAPERS"],
      [String(cfg.read.read), "已读 READ"],
      [String(cfg.read.star), "星标 STARRED"],
    ];
    stats.forEach(([num, label], i) => {
      const x = M + i * 312;
      ctx.fillStyle = CARD.ink;
      ctx.font = `700 88px ${CARD.serif}`;
      ctx.fillText(num, x, statY);
      if (i === 0 && cfg.newCount > 0) {
        ctx.textBaseline = "middle";
        cardPill(ctx, x + ctx.measureText(num).width + 16, statY - 62, `+${cfg.newCount} NEW`, CARD.newInk, CARD.newBg, `750 24px ${CARD.sans}`);
        ctx.textBaseline = "alphabetic";
      }
      ctx.fillStyle = CARD.faint;
      ctx.font = `650 22px ${CARD.sans}`;
      ctx.fillText(label, x + 3, statY + 40);
    });

    const cx = M + 172, cy = statY + 300, R = 158, STROKE = 52;
    const total = Math.max(cfg.themes.reduce((a, t) => a + t.count, 0), 1);
    let angle = -Math.PI / 2;
    const gap = cfg.themes.filter(t => t.count > 0).length > 1 ? 0.03 : 0;
    ctx.lineCap = "butt";
    cfg.themes.forEach(t => {
      if (!t.count) return;
      const sweep = t.count / total * Math.PI * 2;
      ctx.beginPath();
      ctx.strokeStyle = t.hex;
      ctx.lineWidth = STROKE;
      ctx.arc(cx, cy, R, angle + gap / 2, angle + sweep - gap / 2);
      ctx.stroke();
      angle += sweep;
    });
    ctx.fillStyle = CARD.ink;
    ctx.font = `700 62px ${CARD.serif}`;
    ctx.textAlign = "center";
    ctx.fillText(String(cfg.papers), cx, cy + 12);
    ctx.fillStyle = CARD.muted;
    ctx.font = `400 22px ${CARD.sans}`;
    ctx.fillText("篇 papers", cx, cy + 46);
    ctx.textAlign = "left";

    const legendX = M + 400, legendRows = cfg.themes.slice(0, 6);
    let ly = cy - R + 6;
    const rowH = Math.min(56, (2 * R) / Math.max(legendRows.length, 1));
    legendRows.forEach(t => {
      ctx.beginPath();
      ctx.fillStyle = t.hex;
      ctx.arc(legendX + 8, ly + 8, 8, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = CARD.ink;
      ctx.font = `500 27px ${CARD.sans}`;
      ctx.fillText(fitText(ctx, t.name, RIGHT - legendX - 110), legendX + 32, ly + 17);
      ctx.fillStyle = CARD.muted;
      ctx.textAlign = "right";
      ctx.fillText(String(t.count), RIGHT, ly + 17);
      ctx.textAlign = "left";
      ly += rowH;
    });

    let sy = cy + R + 84;
    ctx.strokeStyle = CARD.line;
    ctx.lineWidth = 2;
    ctx.beginPath(); ctx.moveTo(M, sy - 44); ctx.lineTo(RIGHT, sy - 44); ctx.stroke();
    ctx.fillStyle = CARD.muted;
    ctx.font = `650 24px ${CARD.sans}`;
    try { ctx.letterSpacing = "3px"; } catch (e) {}
    ctx.fillText("高分期刊 · TOP JOURNALS", M, sy);
    try { ctx.letterSpacing = "0px"; } catch (e) {}
    sy += 22;
    cfg.journals.slice(0, 3).forEach(j => {
      sy += 58;
      ctx.fillStyle = CARD.ink;
      ctx.font = `650 29px ${CARD.sans}`;
      ctx.fillText(fitText(ctx, j.name, 520), M, sy);
      let px = M + 560;
      ctx.textBaseline = "middle";
      if (j.cas) px += cardPill(ctx, px, sy - 9, j.cas, CARD.cas1Ink, CARD.cas1Bg, `650 23px ${CARD.sans}`) + 12;
      if (j.if) px += cardPill(ctx, px, sy - 9, `IF ${j.if}`, CARD.ifInk, CARD.ifBg, `650 23px ${CARD.sans}`) + 12;
      ctx.textBaseline = "alphabetic";
      ctx.fillStyle = CARD.muted;
      ctx.font = `500 26px ${CARD.sans}`;
      ctx.textAlign = "right";
      ctx.fillText(`${j.count} 篇`, RIGHT, sy);
      ctx.textAlign = "left";
    });

    const py = sy + 92;
    ctx.fillStyle = CARD.muted;
    ctx.font = `650 24px ${CARD.sans}`;
    ctx.fillText("阅读进度 · READING", M, py);
    ctx.fillStyle = CARD.ink;
    ctx.font = `700 28px ${CARD.sans}`;
    ctx.textAlign = "right";
    ctx.fillText(`${cfg.read.read} / ${cfg.papers}`, RIGHT, py);
    ctx.textAlign = "left";
    ctx.fillStyle = CARD.track;
    rr(ctx, M, py + 22, W - 2 * M, 16, 8);
    ctx.fill();
    const readW = Math.round((W - 2 * M) * Math.min(cfg.read.read / Math.max(cfg.papers, 1), 1));
    if (readW > 0) {
      ctx.fillStyle = CARD.ok;
      rr(ctx, M, py + 22, Math.max(readW, 16), 16, 8);
      ctx.fill();
    }

    ctx.fillStyle = CARD.faint;
    ctx.font = `400 22px ${CARD.sans}`;
    ctx.textAlign = "center";
    ctx.fillText(cfg.footer || CARD.footer, W / 2, H - 74);
    ctx.textAlign = "left";
    return canvas;
  }
  function exportShareCard(cfg, btn) {
    const canvas = buildShareCardCanvas(cfg);
    canvas.toBlob(blob => {
      if (blob) downloadBlob("文献库分享卡.png", blob);
      if (btn) {
        const old = btn.textContent;
        btn.textContent = "已导出 ✓";
        setTimeout(() => { btn.textContent = old; }, 1400);
      }
    }, "image/png");
  }
  // Debug/preview hook: opening the dashboard with ?sharecard renders the card
  // full-page instead of the dashboard, so it can be screenshotted or inspected.
  function mountShareCardPreview(buildCfg) {
    if (!new URLSearchParams(location.search).has("sharecard")) return false;
    const canvas = buildShareCardCanvas(buildCfg());
    document.body.innerHTML = "";
    document.body.style.margin = "0";
    document.body.style.background = "#555";
    canvas.style.display = "block";
    canvas.style.width = "540px";
    canvas.style.margin = "0 auto";
    document.body.appendChild(canvas);
    return true;
  }
  async function copyText(text, btn, doneHtml) {
    let okCopy = true;
    try { await navigator.clipboard.writeText(text); }
    catch (e) {
      try {
        const ta = document.createElement("textarea");
        ta.value = text; ta.style.position = "fixed"; ta.style.opacity = "0";
        document.body.appendChild(ta); ta.select(); document.execCommand("copy"); ta.remove();
      } catch (e2) { okCopy = false; }
    }
    if (btn) {
      const old = btn.innerHTML;
      btn.innerHTML = okCopy ? (doneHtml || "✓") : "×";
      btn.disabled = true;
      setTimeout(() => { btn.innerHTML = old; btn.disabled = false; }, 1200);
    }
  }
  function trapFocus(container) {
    const prev = document.activeElement;
    function focusables() {
      return Array.prototype.slice.call(
        container.querySelectorAll('a[href], button:not([disabled]), input, select, textarea, [tabindex="0"]')
      ).filter(el => el.getClientRects().length);
    }
    function onKey(e) {
      if (e.key !== "Tab") return;
      const f = focusables();
      if (!f.length) return;
      const first = f[0], last = f[f.length - 1];
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    }
    container.addEventListener("keydown", onKey);
    const f = focusables();
    if (f.length) f[0].focus();
    return function release() {
      container.removeEventListener("keydown", onKey);
      if (prev && prev.focus) { try { prev.focus(); } catch (e) {} }
    };
  }
  function readHash() {
    const h = location.hash.replace(/^#\/?/, "");
    const legacy = h.match(/^paper-(.+)$/);
    if (legacy) return { paper: decodeURIComponent(legacy[1]) };
    const out = {};
    try { new URLSearchParams(h).forEach((v, k) => { out[k] = v; }); } catch (e) {}
    return out;
  }
  function writeHash(obj) {
    const sp = new URLSearchParams();
    Object.keys(obj).forEach(k => {
      const v = obj[k];
      if (v !== null && v !== undefined && v !== "" && v !== false) sp.set(k, v);
    });
    const s = sp.toString();
    try { history.replaceState(null, "", s ? "#" + s : location.pathname + location.search); } catch (e) { location.hash = s; }
  }
  function matchBlob(p) {
    if (!p.__blob) {
      p.__blob = [p.title, p.authors, p.journal, p.abstract, p.publication_date, p.theme, p.subtheme, p.primary_method, p.methods]
        .map(v => String(v || "")).join(" \n ").toLowerCase();
    }
    return p.__blob;
  }
  function matchesQuery(p, q) {
    const terms = String(q || "").trim().toLowerCase().split(/\s+/).filter(Boolean);
    if (!terms.length) return true;
    const blob = matchBlob(p);
    return terms.every(t => blob.includes(t));
  }
  function highlight(text, q) {
    const t = String(text == null ? "" : text);
    const terms = String(q || "").trim().toLowerCase().split(/\s+/).filter(Boolean);
    if (!terms.length) return escapeHtml(t);
    const lower = t.toLowerCase();
    let out = "", i = 0;
    while (i < t.length) {
      let hit = -1, len = 0;
      for (const term of terms) {
        const idx = lower.indexOf(term, i);
        if (idx !== -1 && (hit === -1 || idx < hit)) { hit = idx; len = term.length; }
      }
      if (hit === -1) { out += escapeHtml(t.slice(i)); break; }
      out += escapeHtml(t.slice(i, hit)) + "<mark>" + escapeHtml(t.slice(hit, hit + len)) + "</mark>";
      i = hit + len;
    }
    return out;
  }
  return { reduced, escapeHtml, B, resolveColor, resolveHexLight, casTier, casTagHtml, casLabel,
    fileUrl, yearOf, monthOf, initTheme, initLang, bindSlashFocus,
    initNotes, statusChipHtml, starBtnHtml, notesPanelHtml, bindNotesPanel, renderReadbar,
    exportWriteback, buildShareCardCanvas, exportShareCard, mountShareCardPreview,
    showTip, moveTip, hideTip, bindTip, countUp, debounce, isPlaceholder, detailValueHtml, detailSection,
    splitAuthors, apa, bibtex, csv, download, downloadBlob, copyText, trapFocus, readHash, writeHash, matchesQuery, highlight };
})();
"""


PDF_OPEN_HTML = r"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Open Local PDF</title>
  <script>__THEME_BOOT__</script>
  <style>
__SHARED_CSS__
    body { min-height:100vh; display:grid; place-items:center; }
    main { width:min(760px, calc(100vw - 28px)); padding:20px 0; }
    article { border:1px solid var(--line); border-radius:14px; background:var(--panel); padding:24px; box-shadow:var(--shadow); border-top:4px solid var(--accent); }
    h1 { font-size:23px; line-height:1.3; }
    .meta, .note { color:var(--muted); font-size:13px; line-height:1.55; margin-top:8px; }
    .actions { display:flex; flex-wrap:wrap; gap:8px; margin:16px 0; }
    .actions a, .actions button { display:inline-flex; align-items:center; border:1px solid var(--line); border-radius:9px; min-height:36px; padding:8px 12px; background:var(--panel); color:var(--link); text-decoration:none; cursor:pointer; }
    .actions .primary { background:var(--accent); border-color:var(--accent); color:#fff; }
    code { display:block; white-space:pre-wrap; overflow-wrap:anywhere; border:1px solid var(--line); border-radius:9px; padding:10px; background:var(--panel-2); color:var(--ink); font-size:12px; }
  </style>
</head>
<body>
<main><article>
  <h1 id="title">Loading PDF...</h1>
  <p class="meta" id="meta"></p>
  <div class="actions" id="actions"></div>
  <p class="note">如果 in-app browser 的 PDF viewer 黑屏，请用“下载 PDF”或“复制文件路径”在 Edge/Chrome/Adobe Reader 打开。<br>If the in-app browser PDF viewer stays black, download the PDF or copy the path and open it in a desktop reader.</p>
  <code id="path"></code>
</article></main>
<script src="__DATA_FILE__"></script>
<script>
  const params = new URLSearchParams(location.search);
  const rank = params.get("rank");
  const papers = (window.__SLR_DASHBOARD_DATA__ && window.__SLR_DASHBOARD_DATA__.papers) || [];
  const paper = papers.find(item => String(item.rank) === String(rank));
  function escapeHtml(value) {
    return String(value || "").replace(/[&<>"']/g, ch => ({ "&":"&amp;", "<":"&lt;", ">":"&gt;", "\"":"&quot;", "'":"&#39;" }[ch]));
  }
  function fileUrl(path) { return path ? encodeURI("file:///" + String(path).replace(/\\/g, "/")) : ""; }
  if (!paper) {
    document.getElementById("title").textContent = "PDF not found";
    document.getElementById("meta").textContent = "No paper matches this rank.";
  } else {
    const pdfHref = fileUrl(paper.local_pdf_path);
    document.getElementById("title").textContent = `#${paper.rank} ${paper.title}`;
    document.getElementById("meta").textContent = `${paper.journal || "Metadata missing"} · ${paper.publication_date || ""}`;
    document.getElementById("path").textContent = paper.local_pdf_path || "";
    document.getElementById("actions").innerHTML = [
      pdfHref ? `<a class="primary" href="${pdfHref}">直接打开 PDF / Open PDF</a>` : "",
      pdfHref ? `<a href="${pdfHref}" download>下载 PDF / Download PDF</a>` : "",
      `<button type="button" id="copyPath">复制文件路径 / Copy path</button>`,
      `<a href="__DASHBOARD_FILE__#paper=${encodeURIComponent(paper.rank)}">返回 Dashboard / Back</a>`
    ].filter(Boolean).join("");
    document.getElementById("copyPath").addEventListener("click", async () => {
      try { await navigator.clipboard.writeText(paper.local_pdf_path || ""); } catch (e) {}
      document.getElementById("copyPath").textContent = "已复制 / Copied";
    });
  }
</script>
</body>
</html>
"""

PDF_OPEN_HTML = PDF_OPEN_HTML.replace("__THEME_BOOT__", THEME_BOOT_JS).replace("__SHARED_CSS__", SHARED_CSS)
