#!/usr/bin/env python3
"""Render the large-library dashboard layout for 100+ paper collections."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from dashboard_common import PDF_OPEN_HTML, SHARED_CSS, SHARED_JS, THEME_BOOT_JS, inline_js_tag, write_js


LARGE_LIBRARY_HTML = r"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Zotero Large Library Dashboard</title>
  <script>__THEME_BOOT__</script>
  <style>
__SHARED_CSS__
    main { width:min(1380px, calc(100vw - 32px)); margin:0 auto; padding:22px 0 42px; }
    h1 { font-size:29px; line-height:1.16; }
    h2 { font-size:18px; line-height:1.3; }
    h3 { font-size:15px; line-height:1.3; }
    .hero { display:grid; grid-template-columns:1.12fr .88fr; gap:12px; align-items:stretch; margin-bottom:12px; }
    .intro { padding:18px 20px; display:flex; flex-direction:column; }
    .intro .brandline { margin-bottom:13px; }
    .intro-top { display:flex; justify-content:space-between; gap:12px; align-items:flex-start; }
    .intro-heading h1 { margin-top:6px; }
    .subtitle { color:var(--muted); font-size:12.5px; line-height:1.5; margin-top:8px; }
    .intro .searchbar { margin-top:auto; padding-top:12px; }
    .kpis { grid-template-columns:repeat(3,minmax(0,1fr)); gap:8px; }
    .kpi { padding:13px; min-height:86px; }
    .kpi .value { font-size:26px; }
    .tabs { display:flex; gap:6px; flex-wrap:wrap; margin:12px 0; }
    .tab { min-width:120px; }
    .tab.active { background:var(--btn-active-bg); color:var(--btn-active-ink); border-color:var(--btn-active-bg); }
    .view { display:none; }
    .view.active { display:block; }
    .stack { display:grid; gap:12px; }
    .bars.cols2 { column-gap:34px; }
    .core-grid { display:grid; gap:8px 22px; }
    .core-grid .core-item { margin-bottom:0; }
    .theme-viz { display:grid; grid-template-columns:232px minmax(0,1fr); gap:24px; align-items:center; }
    .donut-wrap { position:relative; width:210px; height:210px; margin:0 auto; }
    .donut { width:210px; height:210px; display:block; }
    .donut-track { fill:none; stroke:var(--track); stroke-width:22; }
    .segment { fill:none; stroke-width:22; cursor:pointer; transition:stroke-width .18s ease, opacity .18s ease; }
    .segment:hover, .segment.active { stroke-width:27; }
    .donut-center { position:absolute; inset:56px; display:grid; place-content:center; text-align:center; border-radius:999px; background:var(--panel); border:1px solid var(--line); }
    .donut-center strong { font-size:31px; line-height:1; font-variant-numeric:tabular-nums; font-family:var(--font-display); font-weight:640; }
    .donut-center span { color:var(--muted); font-size:11px; margin-top:5px; }
    .theme-block.hl { border-color:var(--accent); box-shadow:inset 0 0 0 1px var(--accent); }
    .bar.hl { background:var(--chip-bg); }
    .yp-axis { stroke:var(--line-strong); stroke-width:1.5; }
    .yp-track { fill:none; stroke:var(--track); }
    .yp-seg { fill:none; transition:stroke-width .15s ease; }
    .yp-hit { fill:transparent; cursor:pointer; }
    .yp-node.hl .yp-seg { stroke-width:13; }
    .yp-count { font-size:12px; font-weight:700; fill:var(--ink); text-anchor:middle; font-variant-numeric:tabular-nums; pointer-events:none; }
    .yp-year { font-size:12.5px; font-weight:700; fill:var(--ink); text-anchor:middle; pointer-events:none; font-variant-numeric:tabular-nums; }
    .tip-flex { display:flex; gap:11px; align-items:center; margin-top:7px; }
    .tip-legend { display:grid; gap:4px; min-width:0; }
    .tip-row { display:flex; gap:6px; align-items:center; font-size:11.5px; white-space:nowrap; }
    .tip-row i { width:8px; height:8px; border-radius:999px; flex:0 0 auto; display:inline-block; }
    .tip-row b { font-variant-numeric:tabular-nums; margin-left:auto; padding-left:8px; }
    .tip-divider { border-top:1px solid var(--line); margin:7px 0 5px; }
    .panel { padding:16px; overflow:hidden; }
    .panel-head { display:flex; align-items:flex-start; justify-content:space-between; gap:10px; margin-bottom:12px; }
    .panel-head .hint { margin-top:4px; }
    .theme-stack { display:grid; gap:10px; }
    .theme-block { border:1px solid var(--line); border-radius:8px; background:var(--panel-2); padding:12px; }
    .theme-top { display:grid; grid-template-columns:10px 1fr auto; gap:9px; align-items:center; margin-bottom:9px; cursor:pointer; border-radius:6px; }
    .theme-top:hover h3 { text-decoration:underline; }
    .theme-top strong { font-variant-numeric:tabular-nums; }
    .dot { width:10px; height:10px; border-radius:999px; display:block; }
    .subchips { display:flex; gap:6px; flex-wrap:wrap; }
    .subchip { border:1px solid var(--line); border-radius:999px; padding:4px 9px; font-size:12px; color:var(--ink); background:var(--panel); min-height:0; }
    .subchip:hover { border-color:var(--accent); color:var(--accent); }
    .explore { display:grid; grid-template-columns:minmax(330px,370px) minmax(0,1fr); gap:14px; align-items:start; }
    .explore > aside.panel { position:sticky; top:12px; }
    .seg { display:grid; grid-template-columns:repeat(3,1fr); gap:0; border:1px solid var(--line); border-radius:8px; overflow:hidden; margin-top:12px; }
    .seg button { border:0; border-radius:0; min-height:34px; font-size:12.5px; background:transparent; }
    .seg button + button { border-left:1px solid var(--line); }
    .seg button[aria-pressed="true"] { background:var(--btn-active-bg); color:var(--btn-active-ink); }
    .tree { display:grid; gap:3px; max-height:64vh; overflow:auto; padding-right:4px; margin-top:10px; }
    .tree-node { width:100%; text-align:left; display:grid; grid-template-columns:1fr auto; gap:8px; align-items:center; border-color:transparent; background:transparent; border-radius:7px; min-height:36px; }
    .tree-node.with-dot { grid-template-columns:10px 1fr auto; }
    .tree-node:hover { background:var(--panel-2); border-color:var(--line); }
    .tree-node[aria-pressed="true"] { background:var(--btn-active-bg); color:var(--btn-active-ink); border-color:var(--btn-active-bg); }
    .tree-node .tn-label { min-width:0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; font-size:13px; font-weight:600; }
    .tree-node.sub { margin-left:16px; min-height:32px; border-left:2px solid var(--line); border-radius:0 7px 7px 0; }
    .tree-node.sub .tn-label { font-size:12px; font-weight:500; }
    .tree-count { color:var(--muted); font-size:11px; font-variant-numeric:tabular-nums; }
    .tree-node[aria-pressed="true"] .tree-count { color:inherit; }
    .results-head { display:flex; align-items:center; justify-content:space-between; gap:10px; margin-bottom:10px; flex-wrap:wrap; }
    .results-actions { display:flex; justify-content:flex-end; gap:8px; flex-wrap:wrap; }
    .subtheme-list { display:grid; gap:9px; }
    .subtheme-card { background:var(--panel); border:1px solid var(--line); border-radius:8px; overflow:hidden; border-left:3px solid var(--chip-line); }
    .subtheme-title { width:100%; border:0; border-radius:0; background:var(--panel-2); min-height:42px; display:grid; grid-template-columns:1fr auto; gap:10px; align-items:center; text-align:left; padding:10px 13px; }
    .subtheme-title span { color:var(--muted); font-size:12px; }
    .year-list { display:grid; gap:6px; border-top:1px solid var(--line); background:var(--panel-2); padding:9px 11px; }
    .year-card { border:1px solid var(--line); border-radius:6px; overflow:hidden; background:var(--panel); }
    .year-title { width:100%; border:0; border-radius:0; background:var(--panel); min-height:36px; display:grid; grid-template-columns:1fr auto; gap:10px; align-items:center; text-align:left; padding:8px 10px; font-size:13px; }
    .year-title span { color:var(--muted); font-size:12px; }
    .year-title:hover { background:var(--panel-2); }
    .paper-rows { display:grid; gap:1px; background:var(--line); border-top:1px solid var(--line); }
    .paper-row { display:grid; grid-template-columns:30px minmax(0,1fr) 84px 150px 138px 44px; gap:10px; align-items:center; min-height:40px; background:var(--panel); border:0; border-radius:0; text-align:left; padding:8px 11px; }
    .paper-row:hover { background:var(--panel-2); }
    .row-flags { display:inline-flex; gap:3px; align-items:center; justify-content:flex-start; font-size:12px; }
    .row-flags .st { color:var(--star); }
    .row-flags .rd { width:8px; height:8px; border-radius:999px; background:var(--ok); display:inline-block; }
    .row-flags .rg { width:8px; height:8px; border-radius:999px; background:var(--reading); display:inline-block; }
    .paper-title { min-width:0; color:var(--link); font-weight:640; font-size:13px; line-height:1.3; }
    .paper-meta { color:var(--muted); font-size:11px; line-height:1.25; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
    .journal-info { border-top:1px solid var(--line); background:var(--panel-2); padding:11px; display:grid; gap:10px; }
    .journal-facts { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:8px; }
    .journal-fact { border:1px solid var(--line); border-radius:6px; background:var(--panel); padding:9px; min-width:0; }
    .journal-fact span { display:block; color:var(--muted); font-size:11px; margin-bottom:3px; }
    .journal-fact strong, .journal-fact a { color:var(--ink); font-size:12px; line-height:1.3; overflow-wrap:anywhere; }
    .journal-fact a { color:var(--link); }
    .flow-wrap { overflow-x:auto; }
    .flow-svg { width:100%; min-width:780px; display:block; }
    .ribbon { fill:none; cursor:pointer; opacity:.55; transition:opacity .18s ease; }
    .ribbon:hover { opacity:.92; }
    .relation-label { font-size:12.5px; font-weight:650; cursor:pointer; fill:var(--ink); }
    .relation-label:hover { text-decoration:underline; }
    .relation-label tspan.cnt { fill:var(--muted); font-weight:500; font-size:11.5px; }
    .relation-label tspan.l2 { fill:var(--muted); font-weight:500; font-size:11px; }
    .relation-sub { font-size:10.5px; fill:var(--muted); letter-spacing:.1em; font-weight:650; }
    .node-dot { cursor:pointer; }
    .core-item { display:grid; grid-template-columns:auto minmax(0,1fr); gap:9px; align-items:start; border:1px solid var(--line); border-radius:9px; padding:8px 10px; margin-bottom:8px; cursor:pointer; background:var(--panel); }
    .core-item:hover { border-color:var(--line-strong); background:var(--panel-2); }
    .core-item .cnum { font-family:var(--font-display); font-weight:700; font-size:19px; color:var(--accent); line-height:1.1; min-width:22px; text-align:center; }
    .core-item .cnum span { display:block; font-size:9px; color:var(--muted); font-weight:500; }
    .core-item strong { font-size:12px; line-height:1.35; font-weight:640; display:block; }
    .core-item em { color:var(--muted); font-size:11px; display:block; margin-top:2px; font-style:normal; }
    @media (max-width:1060px) {
      main { width:min(100vw - 24px, 820px); padding-top:16px; }
      .hero, .explore { grid-template-columns:minmax(0,1fr); }
      .bars.cols2, .core-grid {
        grid-template-columns:minmax(0,1fr) !important;
        grid-template-rows:none !important;
        grid-auto-flow:row !important;
      }
      .kpis { grid-template-columns:repeat(2,minmax(0,1fr)); }
      .explore > aside.panel { position:static; }
      .tree { max-height:none; }
      .paper-row { grid-template-columns:30px minmax(0,1fr); }
      .journal-facts { grid-template-columns:minmax(0,1fr); }
      .detail-grid { grid-template-columns:minmax(0,1fr); }
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
          <div class="eyebrow-label"><span class="lz">Zotero 文献库</span><span class="sep"> · </span><span class="le">Zotero Library</span></div>
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
        <div class="note"><span class="lz">PDF 文献（点击清除筛选）</span><span class="sep"> · </span><span class="le">PDF-backed (click to reset)</span></div>
      </div>
      <div class="kpi"><div class="label">Themes</div><div class="value" id="themeCount">0</div>
        <div class="note"><span class="lz">一级主题</span><span class="sep"> · </span><span class="le">primary categories</span></div></div>
      <div class="kpi"><div class="label">Subthemes</div><div class="value" id="subthemeCount">0</div>
        <div class="note"><span class="lz">二级子主题</span><span class="sep"> · </span><span class="le">second-level clusters</span></div></div>
      <div class="kpi"><div class="label">Methods</div><div class="value" id="methodCount">0</div>
        <div class="note"><span class="lz">方法族</span><span class="sep"> · </span><span class="le">method families</span></div></div>
      <div class="kpi"><div class="label">Journals</div><div class="value" id="journalCount">0</div>
        <div class="note"><span class="lz">已知期刊</span><span class="sep"> · </span><span class="le">known sources</span></div></div>
      <div class="kpi" id="kpiPdf"><div class="label">PDFs</div><div class="value" id="pdfCount">0</div>
        <div class="note"><span class="lz">本地 PDF</span><span class="sep"> · </span><span class="le">local files linked</span></div></div>
    </div>
  </section>

  <nav class="tabs" aria-label="Dashboard views">
    <button class="tab active" type="button" data-tab="overview">Overview / 总览</button>
    <button class="tab" type="button" data-tab="explore">Explore / 浏览</button>
  </nav>

  <div class="chipbar" id="chipBar" hidden></div>

  <section class="view active" id="view-overview">
    <div class="stack">
      <article class="panel">
        <div class="panel-head"><div>
          <h2><span class="lz">主题 × 方法关系流图</span><span class="sep"> / </span><span class="le">Theme-Method Flow Map</span></h2>
          <p class="hint"><span class="lz">全库统计：丝带宽度代表该主题-方法组合的文献数。点击丝带到浏览页查看这批文献，点击左右标签按单一维度浏览。</span><span class="sep"> </span><span class="le">Whole-library view: ribbon width = papers in that theme-method pair. Click a ribbon to open those papers in Explore; click side labels to browse one dimension.</span></p>
        </div></div>
        <div class="flow-wrap"><svg class="flow-svg" id="flowSvg"></svg></div>
      </article>
      <article class="panel">
        <div class="panel-head"><div>
          <h2><span class="lz">主题树</span><span class="sep"> / </span><span class="le">Theme Tree</span></h2>
          <p class="hint"><span class="lz">环图显示主题占比；点击扇区、主题或子主题跳到浏览页，直接查看对应文献。</span><span class="sep"> </span><span class="le">The donut shows theme shares; click a slice, theme, or subtheme to open it in the Explore view.</span></p>
        </div></div>
        <div class="theme-viz">
          <div class="donut-wrap">
            <svg class="donut" id="themeDonut" viewBox="0 0 180 180"></svg>
            <div class="donut-center"><strong id="themeDonutCount">0</strong><span><span class="lz">篇</span><span class="sep"> </span><span class="le">papers</span></span></div>
          </div>
          <div class="theme-stack" id="overviewThemes"></div>
        </div>
      </article>
      <article class="panel">
        <div class="panel-head"><div>
          <h2><span class="lz">方法热度</span><span class="sep"> / </span><span class="le">Method Hotspots</span></h2>
          <p class="hint"><span class="lz">环图显示方法占比；点击扇区或方法条跳到浏览页。</span><span class="sep"> </span><span class="le">The donut shows method shares; click a slice or bar to browse that method.</span></p>
        </div></div>
        <div class="theme-viz">
          <div class="donut-wrap">
            <svg class="donut" id="methodDonut" viewBox="0 0 180 180"></svg>
            <div class="donut-center"><strong id="methodDonutCount">0</strong><span><span class="lz">篇</span><span class="sep"> </span><span class="le">papers</span></span></div>
          </div>
          <div class="bars" id="methodBars"></div>
        </div>
      </article>
      <article class="panel" id="corePanel" hidden>
        <div class="panel-head"><div>
          <h2><span class="lz">核心必读</span><span class="sep"> / </span><span class="le">Most Cited</span></h2>
          <p class="hint"><span class="lz">按集合内被引次数排序（无集合内数据时按全网被引）。点击打开详情。</span><span class="sep"> </span><span class="le">Ranked by in-library citations (falls back to global counts). Click to open details.</span></p>
        </div></div>
        <div id="coreList"></div>
      </article>
      <article class="panel">
        <div class="panel-head"><div>
          <h2><span class="lz">Top 期刊</span><span class="sep"> / </span><span class="le">Top Journals</span></h2>
          <p class="hint"><span class="lz">元数据缺失单独统计，不挤占期刊排行。点击期刊条浏览。</span><span class="sep"> </span><span class="le">Missing metadata is tracked separately; click a bar to browse.</span></p>
        </div></div>
        <div class="bars" id="topJournalBars"></div>
      </article>
      <article class="panel" id="yearPanel" hidden>
        <div class="panel-head"><div>
          <h2><span class="lz">文献时间轴</span><span class="sep"> / </span><span class="le">Library Timeline</span></h2>
          <p class="hint"><span class="lz">每个年份节点是一个小环图：大小 = 当年文献数，扇区 = 当年主题构成。悬停节点看该年的主题/方法明细大图，点击节点到浏览页查看当年文献。</span><span class="sep"> </span><span class="le">Each year node is a mini donut: size = papers that year, slices = that year's theme mix. Hover a node for the detailed theme/method breakdown; click it to open that year in Explore.</span></p>
        </div></div>
        <div class="flow-wrap"><svg class="flow-svg" id="timelineSvg"></svg></div>
      </article>
    </div>
  </section>

  <section class="view" id="view-explore">
    <div class="explore">
      <aside class="panel">
        <h2><span class="lz">浏览维度</span><span class="sep"> / </span><span class="le">Browse</span></h2>
        <div class="seg" id="modeSeg">
          <button type="button" data-mode="theme">主题</button>
          <button type="button" data-mode="method">方法</button>
          <button type="button" data-mode="journal">期刊</button>
        </div>
        <div class="tree" id="themeTree"></div>
      </aside>
      <section class="panel">
        <div class="results-head">
          <div><h2 id="resultTitle"></h2><p class="hint" id="resultHint"></p></div>
          <div class="results-actions">
            <select id="readSelect" title="按阅读状态筛选 / Filter by reading status" style="width:auto;min-height:34px;padding:6px 9px;">
              <option value="">状态：全部 All</option>
              <option value="fresh">NEW 本次新增</option>
              <option value="unread">未读 Unread</option>
              <option value="reading">在读 Reading</option>
              <option value="read">已读 Read</option>
              <option value="starred">★ 星标 Starred</option>
            </select>
            <button type="button" id="expandAllGroups">全部展开 / Expand</button>
            <button type="button" id="collapseAllGroups">收起 / Collapse</button>
            <button type="button" id="exportCsv" title="导出当前筛选（含我的笔记）/ Export current view incl. notes">CSV</button>
            <button type="button" id="exportBib" title="导出当前筛选 / Export current view">BibTeX</button>
            <button type="button" id="exportZotero" title="导出 Zotero 回写包：分类/阅读状态/笔记，配合 zotero_api_import.py write-back 同步回 Zotero / Export write-back package for Zotero sync">Zotero</button>
          </div>
        </div>
        <div class="subtheme-list" id="paperGroups"></div>
      </section>
    </div>
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
const assignments = spec.paper_assignments || {};
const palette = ["#2a78d6","#eb6834","#1baf7a","#eda100","#e87ba4","#008300","#4a3aa7","#e34948"];
const esc = S.escapeHtml, B = S.B;
const MISSING_JOURNAL = "Metadata missing / 元数据缺失";
const notes = S.initNotes(`slr-notes:${spec.title || "zotero-library"}|${papers.length}`);
const citeEdges = ((data.citations && data.citations.edges) || []).filter(e =>
  papers.some(p => String(p.rank) === String(e.source)) && papers.some(p => String(p.rank) === String(e.target)));
const inSetMap = (function () {
  const m = new Map();
  citeEdges.forEach(e => m.set(String(e.target), (m.get(String(e.target)) || 0) + 1));
  papers.forEach(p => { const k = String(p.rank); m.set(k, Math.max(m.get(k) || 0, p.in_set_cited || 0)); });
  return m;
})();
function inSetCited(p) { return inSetMap.get(String(p.rank)) || 0; }

const state = { tab: "overview", mode: "theme", q: "", theme: null, sub: null, method: null, journal: null, year: null, pdf: null, read: null };
let activeRank = null;
let releaseFocus = null;
let navList = papers;
const expandedGroups = new Set();
const expandedYears = new Set();

function paperAssign(p) { return assignments[String(p.rank)] || {}; }
function paperTheme(p) { return paperAssign(p).theme || p.theme || "General / 综合交叉"; }
function paperSubtheme(p) { return paperAssign(p).subtheme || p.subtheme || "General / 综合交叉"; }
function paperMethod(p) { return paperAssign(p).method || p.primary_method || "Other / 其他"; }
function paperYear(p) { return S.yearOf(p) || "Unknown year / 年份未知"; }
function knownJournal(p) { return p.journal && p.journal !== "Zotero local library" ? p.journal : ""; }
function displayJournal(p) { return knownJournal(p) || MISSING_JOURNAL; }
function isMissingJournalName(name) { return String(name || "").startsWith("Metadata missing"); }
function colorForTheme(theme) {
  const idx = themeDefs.findIndex(item => item.name === theme);
  return S.resolveColor((themeDefs[idx] && themeDefs[idx].color) || palette[Math.max(idx, 0) % palette.length]);
}
const methodDefs = spec.method_definitions || [];
function colorForMethod(method) {
  const idx = methodDefs.findIndex(item => item.name === method);
  return S.resolveColor((methodDefs[idx] && methodDefs[idx].color) || palette[Math.max(idx, 0) % palette.length]);
}
function countBy(rows, fn) {
  const map = new Map();
  rows.forEach(row => { const key = fn(row); map.set(key, (map.get(key) || 0) + 1); });
  return [...map.entries()].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));
}
function pdfLauncherUrl(paper) { return "__PDF_OPEN_FILE__?rank=" + encodeURIComponent(paper.rank); }

function passes(p, skip) {
  if (skip !== "q" && state.q && !S.matchesQuery(p, state.q)) return false;
  if (skip !== "theme" && state.theme && paperTheme(p) !== state.theme) return false;
  if (skip !== "sub" && state.sub && paperSubtheme(p) !== state.sub) return false;
  if (skip !== "method" && state.method && paperMethod(p) !== state.method) return false;
  if (skip !== "journal" && state.journal && displayJournal(p) !== state.journal) return false;
  if (skip !== "year" && state.year && paperYear(p) !== state.year) return false;
  if (skip !== "pdf" && state.pdf === "missing" && p.local_pdf_path) return false;
  if (skip !== "read" && state.read) {
    if (state.read === "fresh") { if (!p.is_new) return false; }
    else if (!notes.matches(p.rank, state.read)) return false;
  }
  return true;
}
function filteredPapers() { return papers.filter(p => passes(p, null)); }
function facetEntries(keyFn, skip) {
  const map = new Map();
  papers.forEach(p => { if (passes(p, skip)) { const k = keyFn(p); map.set(k, (map.get(k) || 0) + 1); } });
  return map;
}
function clearFilters() {
  state.q = ""; state.theme = null; state.sub = null; state.method = null; state.journal = null; state.year = null; state.pdf = null; state.read = null;
  document.getElementById("searchInput").value = "";
  document.getElementById("readSelect").value = "";
  recomputeExpansion();
  renderAll();
}

function categoryForPaper(p) {
  if (state.mode === "method") return paperMethod(p);
  if (state.mode === "journal") return displayJournal(p);
  if (state.theme) return paperSubtheme(p);
  return paperTheme(p);
}
function groupByCategory(rows) {
  const byCategory = new Map();
  rows.forEach(p => {
    const key = categoryForPaper(p);
    if (!byCategory.has(key)) byCategory.set(key, []);
    byCategory.get(key).push(p);
  });
  return byCategory;
}
function groupStateKey(name) { return `${state.mode}::${state.theme || ""}::${name}`; }
function yearStateKey(group, year) { return `${group}::${year}`; }
function recomputeExpansion() {
  expandedGroups.clear();
  expandedYears.clear();
  const rows = filteredPapers();
  const groups = groupByCategory(rows);
  const specific = !!(state.theme || state.sub || state.method || state.journal || state.q || state.year || state.pdf);
  if (!specific && rows.length > 40) return;
  groups.forEach((items, name) => {
    const key = groupStateKey(name);
    expandedGroups.add(key);
    if (items.length <= 12 || groups.size === 1) {
      countBy(items, paperYear).forEach(([year]) => expandedYears.add(yearStateKey(key, year)));
    }
  });
}

function renderOverview() {
  document.getElementById("overviewThemes").innerHTML = themeDefs.map((def, index) => {
    const theme = def.name;
    const rows = papers.filter(p => paperTheme(p) === theme);
    const subs = countBy(rows, paperSubtheme).slice(0, 8);
    return `<section class="theme-block">
      <div class="theme-top" role="button" tabindex="0" data-theme="${esc(theme)}">
        <i class="dot" style="background:${def.color || palette[index % palette.length]}"></i>
        <h3>${esc(theme)}</h3><strong>${rows.length}</strong>
      </div>
      <div class="subchips">${subs.map(([name, count]) =>
        `<button class="subchip" type="button" data-theme="${esc(theme)}" data-sub="${esc(name)}">${esc(name)} · ${count}</button>`).join("")}</div>
    </section>`;
  }).join("");
  document.querySelectorAll("#overviewThemes .theme-top").forEach(el => {
    const go = () => gotoExplore({ mode: "theme", theme: el.dataset.theme, sub: null });
    el.addEventListener("click", go);
    el.addEventListener("keydown", e => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); go(); } });
  });
  document.querySelectorAll("#overviewThemes .subchip").forEach(el =>
    el.addEventListener("click", () => gotoExplore({ mode: "theme", theme: el.dataset.theme, sub: el.dataset.sub })));
  document.querySelectorAll("#overviewThemes .theme-block").forEach(block => {
    const name = (block.querySelector(".theme-top") || {}).dataset ? block.querySelector(".theme-top").dataset.theme : "";
    block.addEventListener("mouseenter", () => {
      const seg = document.querySelector(`#themeDonut .segment[data-theme="${CSS.escape(name)}"]`);
      if (seg) seg.classList.add("active");
    });
    block.addEventListener("mouseleave", () => {
      const seg = document.querySelector(`#themeDonut .segment[data-theme="${CSS.escape(name)}"]`);
      if (seg) seg.classList.remove("active");
    });
  });
  renderThemeDonut();

  renderBars("methodBars", countBy(papers, paperMethod).slice(0, 10), "var(--ok)", name => gotoExplore({ mode: "method", method: name }));
  renderBars("topJournalBars", countBy(papers.filter(knownJournal), knownJournal).slice(0, 10), "var(--accent)", name => gotoExplore({ mode: "journal", journal: name }));
  renderCorePanel();
  renderMethodDonut();
  renderYearTimeline();
  document.querySelectorAll("#methodBars .bar").forEach(bar => {
    const name = bar.dataset.name;
    bar.addEventListener("mouseenter", () => {
      const seg = document.querySelector(`#methodDonut .segment[data-method="${CSS.escape(name)}"]`);
      if (seg) seg.classList.add("active");
    });
    bar.addEventListener("mouseleave", () => {
      const seg = document.querySelector(`#methodDonut .segment[data-method="${CSS.escape(name)}"]`);
      if (seg) seg.classList.remove("active");
    });
  });
}
function renderBars(targetId, rows, color, onClick) {
  const max = Math.max(...rows.map(([, n]) => n), 1);
  const box = document.getElementById(targetId);
  box.innerHTML = rows.map(([name, count]) => `
    <div class="bar" role="button" tabindex="0" data-name="${esc(name)}">
      <div class="bar-name">${esc(name)}<span class="sub">${count} ${count === 1 ? "paper" : "papers"}</span></div>
      <div class="track"><div class="fill" style="width:${Math.max(5, Math.round(count / max * 100))}%;background:${color};"></div></div>
      <div class="count">${count}</div>
    </div>`).join("");
  // Full-width panels split long rankings into two column-major columns
  // (1..N/2 left, rest right) so bars stay readable instead of stretching.
  if (rows.length > 5) {
    box.classList.add("cols2");
    box.style.gridTemplateColumns = "repeat(2, minmax(0,1fr))";
    box.style.gridTemplateRows = `repeat(${Math.ceil(rows.length / 2)}, auto)`;
    box.style.gridAutoFlow = "column";
  } else {
    box.classList.remove("cols2");
    box.style.gridTemplateColumns = "";
    box.style.gridTemplateRows = "";
    box.style.gridAutoFlow = "";
  }
  box.querySelectorAll(".bar").forEach(bar => {
    bar.addEventListener("click", () => onClick(bar.dataset.name));
    bar.addEventListener("keydown", e => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); onClick(bar.dataset.name); } });
  });
}
let themeDonutBuilt = false;
function renderThemeDonut() {
  if (themeDonutBuilt) return;
  themeDonutBuilt = true;
  const svg = document.getElementById("themeDonut");
  const counts = new Map(countBy(papers, paperTheme));
  const entries = themeDefs.map(d => d.name).filter(name => counts.get(name));
  const total = Math.max(papers.length, 1);
  const R = 67, C = 2 * Math.PI * R;
  const gap = entries.length > 1 ? 2.4 : 0;
  let offset = 0;
  svg.innerHTML = `<circle class="donut-track" cx="90" cy="90" r="${R}"></circle>` + entries.map(name => {
    const n = counts.get(name) || 0;
    const len = n / total * C;
    const seg = Math.max(len - gap, 0.5);
    const el = `<circle class="segment" tabindex="0" role="button" cx="90" cy="90" r="${R}"
      style="stroke:${colorForTheme(name)};stroke-dasharray:${seg} ${C - seg};stroke-dashoffset:${-(offset + gap / 2)}"
      transform="rotate(-90 90 90)" data-theme="${esc(name)}" data-n="${n}" aria-label="${esc(name)}"></circle>`;
    offset += len;
    return el;
  }).join("");
  document.getElementById("themeDonutCount").textContent = papers.length;
  const blockFor = name => [...document.querySelectorAll("#overviewThemes .theme-block")]
    .find(block => (block.querySelector(".theme-top") || { dataset: {} }).dataset.theme === name);
  svg.querySelectorAll(".segment").forEach(el => {
    const name = el.dataset.theme;
    const go = () => gotoExplore({ mode: "theme", theme: name, sub: null });
    el.addEventListener("click", go);
    el.addEventListener("keydown", e => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); go(); } });
    S.bindTip(el, () => `<b>${esc(name)}</b><br>${esc(el.dataset.n)} · ${Math.round(Number(el.dataset.n) / total * 100)}%
      <span class="tip-sub">${B("点击到浏览页查看", "Click to browse in Explore")}</span>`);
    el.addEventListener("mouseenter", () => { const block = blockFor(name); if (block) block.classList.add("hl"); });
    el.addEventListener("mouseleave", () => { const block = blockFor(name); if (block) block.classList.remove("hl"); });
  });
}

let methodDonutBuilt = false;
function methodDonutEntries() {
  const counts = countBy(papers, paperMethod);
  const top = counts.slice(0, 8);
  const restTotal = counts.slice(8).reduce((sum, [, n]) => sum + n, 0);
  const entries = top.map(([name, n]) => ({ name, n, color: colorForMethod(name), other: false }));
  if (restTotal > 0) entries.push({ name: "其他 / Other", n: restTotal, color: "var(--line-strong)", other: true });
  return entries;
}
function renderMethodDonut() {
  if (methodDonutBuilt) return;
  methodDonutBuilt = true;
  const svg = document.getElementById("methodDonut");
  const entries = methodDonutEntries();
  const total = Math.max(papers.length, 1);
  const R = 67, C = 2 * Math.PI * R;
  const gap = entries.length > 1 ? 2.4 : 0;
  let offset = 0;
  svg.innerHTML = `<circle class="donut-track" cx="90" cy="90" r="${R}"></circle>` + entries.map(entry => {
    const len = entry.n / total * C;
    const seg = Math.max(len - gap, 0.5);
    const el = `<circle class="segment" tabindex="0" role="button" cx="90" cy="90" r="${R}"
      style="stroke:${entry.color};stroke-dasharray:${seg} ${C - seg};stroke-dashoffset:${-(offset + gap / 2)}"
      transform="rotate(-90 90 90)" data-method="${esc(entry.name)}" data-n="${entry.n}" data-other="${entry.other ? 1 : ""}"
      aria-label="${esc(entry.name)}"></circle>`;
    offset += len;
    return el;
  }).join("");
  document.getElementById("methodDonutCount").textContent = papers.length;
  svg.querySelectorAll(".segment").forEach(el => {
    const name = el.dataset.method;
    if (!el.dataset.other) {
      const go = () => gotoExplore({ mode: "method", method: name });
      el.addEventListener("click", go);
      el.addEventListener("keydown", e => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); go(); } });
    }
    S.bindTip(el, () => `<b>${esc(name)}</b><br>${esc(el.dataset.n)} · ${Math.round(Number(el.dataset.n) / total * 100)}%
      ${el.dataset.other ? "" : `<span class="tip-sub">${B("点击到浏览页查看", "Click to browse in Explore")}</span>`}`);
    el.addEventListener("mouseenter", () => {
      const bar = document.querySelector(`#methodBars .bar[data-name="${CSS.escape(name)}"]`);
      if (bar) bar.classList.add("hl");
    });
    el.addEventListener("mouseleave", () => {
      const bar = document.querySelector(`#methodBars .bar[data-name="${CSS.escape(name)}"]`);
      if (bar) bar.classList.remove("hl");
    });
  });
}

let timelineBuilt = false;
function renderYearTimeline() {
  const panel = document.getElementById("yearPanel");
  const years = [...new Set(papers.map(paperYear).filter(y => /^\d{4}$/.test(y)))].sort();
  if (years.length < 2) { panel.hidden = true; return; }
  panel.hidden = false;
  if (timelineBuilt) return;
  timelineBuilt = true;
  const shown = years.slice(-12);
  const themes = themeDefs.map(d => d.name).filter(name => papers.some(p => paperTheme(p) === name));
  const byYear = new Map(shown.map(y => [y, []]));
  papers.forEach(p => { const y = paperYear(p); if (byYear.has(y)) byYear.get(y).push(p); });
  const maxN = Math.max(...shown.map(y => byYear.get(y).length), 1);
  const W = 1000, pad = 70, cy = 96;
  const H = 178;
  const svg = document.getElementById("timelineSvg");
  svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
  const xOf = y => pad + (shown.indexOf(y) + 0.5) * ((W - 2 * pad) / shown.length);
  const radius = n => 15 + Math.sqrt(n / maxN) * 14;
  const parts = [`<line class="yp-axis" x1="${pad - 26}" y1="${cy}" x2="${W - pad + 26}" y2="${cy}"></line>`];
  shown.forEach(y => {
    const rows = byYear.get(y);
    const n = rows.length;
    const x = xOf(y), R = radius(n), stroke = 10;
    const C = 2 * Math.PI * R;
    const counts = new Map();
    rows.forEach(p => counts.set(paperTheme(p), (counts.get(paperTheme(p)) || 0) + 1));
    const gap = [...counts.values()].filter(Boolean).length > 1 ? 2 : 0;
    let offset = 0;
    const slices = themes.filter(t => counts.get(t)).map(t => {
      const len = counts.get(t) / Math.max(n, 1) * C;
      const seg = Math.max(len - gap, 0.4);
      const el = `<circle class="yp-seg" cx="${x}" cy="${cy}" r="${R}" stroke="${colorForTheme(t)}" stroke-width="${stroke}"
        stroke-dasharray="${seg} ${C - seg}" stroke-dashoffset="${-(offset + gap / 2)}" transform="rotate(-90 ${x} ${cy})"></circle>`;
      offset += len;
      return el;
    }).join("");
    parts.push(`<g class="yp-node" data-year="${esc(y)}">
      <circle class="yp-track" cx="${x}" cy="${cy}" r="${R}" stroke-width="${stroke}"></circle>
      ${slices}
      <text class="yp-count" x="${x}" y="${cy + 4}">${n}</text>
      <text class="yp-year" x="${x}" y="${cy + R + 22}">${esc(y)}</text>
      <circle class="yp-hit" cx="${x}" cy="${cy}" r="${R + stroke / 2 + 3}"></circle>
    </g>`);
  });
  svg.innerHTML = parts.join("");
  const tipPie = (entries, total) => {
    const R = 30, C = 2 * Math.PI * R;
    const gap = entries.length > 1 ? 2 : 0;
    let offset = 0;
    const pie = `<svg width="76" height="76" viewBox="0 0 76 76" style="flex:0 0 auto">
      <circle cx="38" cy="38" r="${R}" fill="none" stroke="var(--track)" stroke-width="13"></circle>
      ${entries.map(entry => {
        const len = entry.n / Math.max(total, 1) * C;
        const seg = Math.max(len - gap, 0.4);
        const el = `<circle cx="38" cy="38" r="${R}" fill="none" stroke="${entry.color}" stroke-width="13"
          stroke-dasharray="${seg} ${C - seg}" stroke-dashoffset="${-(offset + gap / 2)}" transform="rotate(-90 38 38)"></circle>`;
        offset += len;
        return el;
      }).join("")}
    </svg>`;
    const legend = entries.map(entry =>
      `<span class="tip-row"><i style="background:${entry.color}"></i>${esc(shortLabel(String(entry.name).split(/\s+\/\s+/)[0], 20))}<b>${entry.n}</b></span>`).join("");
    return `<div class="tip-flex">${pie}<span class="tip-legend">${legend}</span></div>`;
  };
  const yearTipHtml = y => {
    const rows = byYear.get(y);
    const n = rows.length;
    const themeEntries = countBy(rows, paperTheme).map(([t, c]) => ({ name: t, n: c, color: colorForTheme(t) }));
    const methodAll = countBy(rows, paperMethod);
    const methodEntries = methodAll.slice(0, 5).map(([m, c]) => ({ name: m, n: c, color: colorForMethod(m) }));
    const rest = methodAll.slice(5).reduce((sum, [, c]) => sum + c, 0);
    if (rest > 0) methodEntries.push({ name: "其他 / Other", n: rest, color: "var(--line-strong)" });
    return `<b>${esc(y)} · ${n} ${B("篇", "papers")}</b>
      <span class="tip-sub" style="margin-top:6px">${B("主题构成", "Themes")}</span>
      ${tipPie(themeEntries, n)}
      <div class="tip-divider"></div>
      <span class="tip-sub">${B("方法构成", "Methods")}</span>
      ${tipPie(methodEntries, n)}
      <span class="tip-sub" style="margin-top:6px">${B("点击查看当年文献", "Click to open this year in Explore")}</span>`;
  };
  svg.querySelectorAll(".yp-node").forEach(node => {
    const y = node.dataset.year;
    const hit = node.querySelector(".yp-hit");
    hit.addEventListener("click", () => gotoExplore({ year: y }));
    hit.addEventListener("mouseenter", () => node.classList.add("hl"));
    hit.addEventListener("mouseleave", () => node.classList.remove("hl"));
    S.bindTip(hit, () => yearTipHtml(y));
  });
}

function gotoExplore(patch) {
  if (patch.mode && patch.mode !== state.mode) {
    state.mode = patch.mode;
    state.theme = null; state.sub = null; state.method = null; state.journal = null;
  }
  if ("theme" in patch) state.theme = patch.theme;
  if ("sub" in patch) state.sub = patch.sub;
  if ("method" in patch) state.method = patch.method;
  if ("journal" in patch) state.journal = patch.journal;
  if ("year" in patch) state.year = patch.year;
  state.tab = "explore";
  recomputeExpansion();
  renderAll();
}

function renderTree() {
  document.querySelectorAll("#modeSeg button").forEach(btn => btn.setAttribute("aria-pressed", btn.dataset.mode === state.mode));
  const tree = document.getElementById("themeTree");
  const rows = [];
  if (state.mode === "theme") {
    const counts = facetEntries(paperTheme, "theme");
    rows.push(`<button class="tree-node" type="button" data-act="all" aria-pressed="${!state.theme}"><span class="tn-label">${B("全部主题", "All themes")}</span><span class="tree-count">${filteredCountIgnoring("theme")}</span></button>`);
    themeDefs.forEach(def => {
      const n = counts.get(def.name) || 0;
      const selected = state.theme === def.name;
      rows.push(`<button class="tree-node with-dot" type="button" data-theme="${esc(def.name)}" aria-pressed="${selected && !state.sub}"><i class="dot" style="background:${def.color}"></i><span class="tn-label">${esc(def.name)}</span><span class="tree-count">${n}</span></button>`);
      if (selected) {
        const subCounts = new Map();
        papers.forEach(p => {
          if (paperTheme(p) === def.name && passes(p, "sub")) {
            const k = paperSubtheme(p);
            subCounts.set(k, (subCounts.get(k) || 0) + 1);
          }
        });
        [...subCounts.entries()].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0])).forEach(([name, count]) => {
          rows.push(`<button class="tree-node sub" type="button" data-sub="${esc(name)}" aria-pressed="${state.sub === name}"><span class="tn-label">${esc(name)}</span><span class="tree-count">${count}</span></button>`);
        });
      }
    });
  } else if (state.mode === "method") {
    const counts = facetEntries(paperMethod, "method");
    rows.push(`<button class="tree-node" type="button" data-act="all" aria-pressed="${!state.method}"><span class="tn-label">${B("全部方法", "All methods")}</span><span class="tree-count">${filteredCountIgnoring("method")}</span></button>`);
    [...counts.entries()].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0])).forEach(([name, n]) => {
      rows.push(`<button class="tree-node" type="button" data-method="${esc(name)}" aria-pressed="${state.method === name}"><span class="tn-label">${esc(name)}</span><span class="tree-count">${n}</span></button>`);
    });
  } else {
    const counts = facetEntries(displayJournal, "journal");
    rows.push(`<button class="tree-node" type="button" data-act="all" aria-pressed="${!state.journal}"><span class="tn-label">${B("全部期刊", "All journals")}</span><span class="tree-count">${filteredCountIgnoring("journal")}</span></button>`);
    const entries = [...counts.entries()].sort((a, b) => {
      const am = isMissingJournalName(a[0]), bm = isMissingJournalName(b[0]);
      if (am !== bm) return am ? 1 : -1;
      return b[1] - a[1] || a[0].localeCompare(b[0]);
    });
    entries.forEach(([name, n]) => {
      rows.push(`<button class="tree-node" type="button" data-journal="${esc(name)}" aria-pressed="${state.journal === name}"><span class="tn-label">${esc(name)}</span><span class="tree-count">${n}</span></button>`);
    });
  }
  tree.innerHTML = rows.join("");
  tree.querySelectorAll(".tree-node").forEach(btn => btn.addEventListener("click", () => {
    if (btn.dataset.act === "all") { state.theme = null; state.sub = null; state.method = null; state.journal = null; }
    else if (btn.dataset.theme) {
      const name = btn.dataset.theme;
      if (state.theme === name && !state.sub) { state.theme = null; }
      else { state.theme = name; }
      state.sub = null;
    }
    else if (btn.dataset.sub) { state.sub = state.sub === btn.dataset.sub ? null : btn.dataset.sub; }
    else if (btn.dataset.method) { state.method = state.method === btn.dataset.method ? null : btn.dataset.method; }
    else if (btn.dataset.journal) { state.journal = state.journal === btn.dataset.journal ? null : btn.dataset.journal; }
    recomputeExpansion();
    renderAll();
  }));
}
function filteredCountIgnoring(skip) {
  return papers.filter(p => passes(p, skip)).length;
}

function renderExplore() {
  renderTree();
  const rows = filteredPapers();
  const title = state.mode === "method" ? B("方法分类", "Methods") : state.mode === "journal" ? B("期刊列表", "Journals") : (state.theme ? B("子主题", "Subthemes") : B("主题分类", "Themes"));
  document.getElementById("resultTitle").innerHTML = title;
  document.getElementById("resultHint").innerHTML = B(`${rows.length} 篇文章`, `${rows.length} papers`);
  if (state.mode === "journal") renderJournalGroups(rows);
  else renderCategoryGroups(rows);
}
function renderCategoryGroups(rows) {
  const byCategory = groupByCategory(rows);
  const groups = [...byCategory.entries()].sort((a, b) => b[1].length - a[1].length || a[0].localeCompare(b[0]));
  document.getElementById("paperGroups").innerHTML = groups.map(([name, items]) => {
    const key = groupStateKey(name);
    const expanded = expandedGroups.has(key);
    return `<section class="subtheme-card">
      <button class="subtheme-title" type="button" data-group-key="${esc(key)}" aria-expanded="${expanded}"><strong>${esc(name)}</strong><span>${items.length} papers · ${expanded ? "收起 / Collapse" : "展开 / Expand"}</span></button>
      ${expanded ? yearGroupsHtml(key, items) : ""}
    </section>`;
  }).join("") || `<p class="hint">${B("没有匹配的文章", "No matching papers")}</p>`;
  bindPaperGroupEvents();
}
function homepageForJournal(items) {
  const hit = items.find(p => p.homepage_url || p.official_if_evidence_url);
  return hit ? (hit.homepage_url || hit.official_if_evidence_url || "") : "";
}
function impactFactorForJournal(items) {
  const values = items.map(p => Number(p.official_impact_factor || 0)).filter(Boolean);
  if (values.length) return Math.max(...values).toFixed(1);
  const text = items.map(p => String(p.official_impact_factor || "").trim()).find(Boolean);
  return text || "";
}
function renderJournalGroups(rows) {
  const byJournal = groupByCategory(rows);
  const groups = [...byJournal.entries()].sort((a, b) => {
    const am = isMissingJournalName(a[0]), bm = isMissingJournalName(b[0]);
    if (am !== bm) return am ? 1 : -1;
    return b[1].length - a[1].length || a[0].localeCompare(b[0]);
  });
  document.getElementById("paperGroups").innerHTML = groups.map(([journal, items]) => {
    const key = groupStateKey(journal);
    const expanded = expandedGroups.has(key);
    const ifValue = impactFactorForJournal(items);
    const casHit = items.find(p => S.casTier(p));
    const casSuffix = casHit ? `${S.casLabel(casHit)} · ` : "";
    const suffix = /^\d+(\.\d+)?$/.test(String(ifValue)) ? `${casSuffix}IF ${ifValue} · ` : casSuffix;
    return `<section class="subtheme-card">
      <button class="subtheme-title" type="button" data-group-key="${esc(key)}" aria-expanded="${expanded}"><strong>${esc(journal)}</strong><span>${suffix}${items.length} papers · ${expanded ? "收起 / Collapse" : "展开 / Expand"}</span></button>
      ${expanded ? `${journalInfoHtml(journal, items)}${yearGroupsHtml(key, items)}` : ""}
    </section>`;
  }).join("") || `<p class="hint">${B("没有匹配的期刊", "No matching journals")}</p>`;
  bindPaperGroupEvents();
}
function journalInfoHtml(journal, items) {
  const homepage = homepageForJournal(items);
  const missingJournal = isMissingJournalName(journal);
  const ifValue = missingJournal ? "N/A - metadata missing" : (impactFactorForJournal(items) || "Verification needed");
  const metadataIssue = missingJournal || String(ifValue).startsWith("N/A - metadata");
  const years = countBy(items, paperYear).map(([year]) => year).join(", ");
  const link = metadataIssue ? "<strong>Repair Zotero metadata first</strong>" : (homepage ? `<a href="${esc(homepage)}" target="_blank" rel="noopener">期刊官网 / Journal homepage</a>` : "<strong>Verification needed</strong>");
  return `<div class="journal-info">
    <div class="journal-facts">
      <div class="journal-fact"><span>期刊 / Journal</span><strong>${esc(journal)}</strong></div>
      <div class="journal-fact"><span>文章数 / Papers</span><strong>${items.length}</strong></div>
      <div class="journal-fact"><span>官方 IF / Official IF</span><strong>${esc(ifValue)}</strong></div>
      <div class="journal-fact"><span>官网 / Source</span>${link}</div>
    </div>
    <div class="journal-fact"><span>年份 / Years</span><strong>${esc(years || "Unknown year / 年份未知")}</strong></div>
  </div>`;
}
function yearGroupsHtml(group, items) {
  const byYear = new Map();
  items.forEach(p => {
    const year = paperYear(p);
    if (!byYear.has(year)) byYear.set(year, []);
    byYear.get(year).push(p);
  });
  const yearGroups = [...byYear.entries()].sort((a, b) => {
    const ay = parseInt(a[0], 10), by = parseInt(b[0], 10);
    const an = Number.isFinite(ay) ? ay : -Infinity;
    const bn = Number.isFinite(by) ? by : -Infinity;
    return bn - an || a[0].localeCompare(b[0]);
  });
  return `<div class="year-list">${yearGroups.map(([year, yearItems]) => {
    const key = yearStateKey(group, year);
    const expanded = expandedYears.has(key);
    return `<section class="year-card">
      <button class="year-title" type="button" data-year-group="${esc(group)}" data-year="${esc(year)}" aria-expanded="${expanded}"><strong>${esc(year)}</strong><span>${yearItems.length} papers · ${expanded ? "收起 / Collapse" : "展开 / Expand"}</span></button>
      ${expanded ? `<div class="paper-rows">${yearItems.map(paperRow).join("")}</div>` : ""}
    </section>`;
  }).join("")}</div>`;
}
function paperRow(p) {
  const entry = notes.get(p.rank);
  const flags = [
    entry.star ? `<span class="st" title="星标 / Starred">★</span>` : "",
    entry.s === "read" ? `<i class="rd" title="已读 / Read"></i>` : (entry.s === "reading" ? `<i class="rg" title="在读 / Reading"></i>` : ""),
  ].filter(Boolean).join("");
  return `<button class="paper-row" type="button" data-rank="${esc(p.rank)}">
    <span class="row-flags">${flags}</span>
    <span class="paper-title">${p.is_new ? `<span class="tag new">NEW</span> ` : ""}#${esc(p.rank)} ${S.highlight(p.title, state.q)}</span>
    <span class="paper-meta">${esc(S.yearOf(p) || "—")}</span>
    <span class="paper-meta">${esc(knownJournal(p) || "Metadata missing")}</span>
    <span class="paper-meta">${esc(paperMethod(p))}</span>
    <span>${p.local_pdf_path ? `<span class="tag pdf">PDF</span>` : ""}</span>
  </button>`;
}
function renderCorePanel() {
  const panel = document.getElementById("corePanel");
  const withInSet = papers.filter(p => inSetCited(p) > 0)
    .sort((a, b) => inSetCited(b) - inSetCited(a) || (b.cited_by_count || 0) - (a.cited_by_count || 0));
  const useGlobal = !withInSet.length;
  const rows = (useGlobal
    ? papers.filter(p => (p.cited_by_count || 0) > 0).sort((a, b) => (b.cited_by_count || 0) - (a.cited_by_count || 0))
    : withInSet).slice(0, 8);
  if (!rows.length) { panel.hidden = true; return; }
  panel.hidden = false;
  const box = document.getElementById("coreList");
  box.className = "core-grid";
  if (rows.length > 4) {
    box.style.gridTemplateColumns = "repeat(2, minmax(0,1fr))";
    box.style.gridTemplateRows = `repeat(${Math.ceil(rows.length / 2)}, auto)`;
    box.style.gridAutoFlow = "column";
  } else {
    box.style.gridTemplateColumns = "";
    box.style.gridTemplateRows = "";
    box.style.gridAutoFlow = "";
  }
  box.innerHTML = rows.map(p => `
    <div class="core-item" data-rank="${esc(p.rank)}">
      <div class="cnum">${useGlobal ? (p.cited_by_count || 0) : inSetCited(p)}<span>${useGlobal ? "cited" : "in-set"}</span></div>
      <div><strong>#${esc(p.rank)} ${esc(p.title)}</strong><em>${esc(knownJournal(p) || "Metadata missing")} · ${esc(paperTheme(p))}</em></div>
    </div>`).join("");
  document.querySelectorAll("#coreList .core-item").forEach(el => el.addEventListener("click", () => openDetail(el.dataset.rank)));
}
function bindPaperGroupEvents() {
  document.querySelectorAll("#paperGroups [data-rank]").forEach(el => el.addEventListener("click", () => openDetail(el.dataset.rank)));
  document.querySelectorAll("#paperGroups [data-year-group]").forEach(el => el.addEventListener("click", event => {
    if (event.target.closest("[data-rank]")) return;
    const key = yearStateKey(el.dataset.yearGroup, el.dataset.year);
    expandedYears.has(key) ? expandedYears.delete(key) : expandedYears.add(key);
    renderExplore();
  }));
  document.querySelectorAll("#paperGroups [data-group-key]").forEach(el => el.addEventListener("click", event => {
    const group = el.dataset.groupKey;
    if (!group || event.target.closest("[data-rank]")) return;
    if (expandedGroups.has(group)) {
      expandedGroups.delete(group);
      const prefix = `${group}::`;
      [...expandedYears].forEach(key => { if (key.startsWith(prefix)) expandedYears.delete(key); });
    } else {
      expandedGroups.add(group);
    }
    renderExplore();
  }));
}

function relationPairs(rows) {
  const map = new Map();
  rows.forEach(p => {
    const key = paperTheme(p) + "|||" + paperMethod(p);
    if (!map.has(key)) map.set(key, { theme: paperTheme(p), method: paperMethod(p), papers: [] });
    map.get(key).papers.push(p);
  });
  return [...map.values()].sort((a, b) => b.papers.length - a.papers.length);
}
function shortLabel(name, max) { const t = String(name); return t.length > max ? t.slice(0, max - 1) + "…" : t; }
let flowBuilt = false;
function renderFlowMap() {
  // Whole-library aggregate, like everything else on the Overview tab; the
  // data never changes after load, so build once.
  if (flowBuilt) return;
  flowBuilt = true;
  const svg = document.getElementById("flowSvg");
  const pairs = relationPairs(papers);
  const themes = themeDefs.map(d => d.name).filter(name => papers.some(p => paperTheme(p) === name));
  const methods = countBy(papers, paperMethod).map(([name]) => name);
  const rows = Math.max(themes.length, methods.length);
  const top = 46, rowGap = Math.max(46, Math.min(64, 400 / Math.max(rows - 1, 1)));
  const bottom = top + (rows - 1) * rowGap;
  const H = bottom + 42;
  svg.setAttribute("viewBox", `0 0 1000 ${H}`);
  const leftX = 262, rightX = 742;
  const centerFor = (n, i) => top + ((rows - n) * rowGap) / 2 + i * rowGap;
  const themeY = new Map(themes.map((name, i) => [name, centerFor(themes.length, i)]));
  const methodY = new Map(methods.map((name, i) => [name, centerFor(methods.length, i)]));
  const max = Math.max(...pairs.map(p => p.papers.length), 1);
  const themeCounts = new Map(countBy(papers, paperTheme));
  const methodCounts = new Map(countBy(papers, paperMethod));
  const ribbons = pairs.map(pair => {
    const y1 = themeY.get(pair.theme) || top;
    const y2 = methodY.get(pair.method) || top;
    const d = `M ${leftX} ${y1} C ${leftX + 175} ${y1}, ${rightX - 175} ${y2}, ${rightX} ${y2}`;
    const width = 3 + Math.round(pair.papers.length / max * 16);
    return `<path class="ribbon" d="${d}" stroke="${colorForTheme(pair.theme)}" stroke-width="${width}"
      data-theme="${esc(pair.theme)}" data-method="${esc(pair.method)}" data-n="${pair.papers.length}"></path>`;
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
    label(name, leftX - 22, themeY.get(name), "end", colorForTheme(name), "theme", themeCounts.get(name) || 0)).join("");
  const rightLabels = methods.map(name =>
    label(name, rightX + 22, methodY.get(name), "start", colorForMethod(name), "method", methodCounts.get(name) || 0)).join("");
  svg.innerHTML = `<text class="relation-sub" x="20" y="18">主题 THEME</text>
    <text class="relation-sub" x="${rightX + 22}" y="18">方法 METHOD</text>${ribbons}${leftLabels}${rightLabels}`;
  svg.querySelectorAll(".ribbon").forEach(path => {
    path.addEventListener("click", () =>
      gotoExplore({ mode: "theme", theme: path.dataset.theme, sub: null, method: path.dataset.method, journal: null }));
    S.bindTip(path, () => `<b>${esc(path.dataset.theme)}</b> × <b>${esc(path.dataset.method)}</b> · ${esc(path.dataset.n)}
      <span class="tip-sub">${B("点击在浏览页查看这批文献", "Click to open these papers in Explore")}</span>`);
  });
  svg.querySelectorAll(".relation-label, .node-dot").forEach(el => {
    el.addEventListener("click", () => {
      if (el.dataset.kind === "theme") gotoExplore({ mode: "theme", theme: el.dataset.name, sub: null });
      else gotoExplore({ mode: "method", method: el.dataset.name });
    });
  });
}

function renderChips() {
  const bar = document.getElementById("chipBar");
  const chips = [];
  const chip = (label, value, clear) => chips.push({ label, value, clear });
  if (state.q) chip(B("搜索", "Search"), state.q, () => { state.q = ""; document.getElementById("searchInput").value = ""; });
  if (state.theme) chip(B("主题", "Theme"), state.theme, () => { state.theme = null; state.sub = null; });
  if (state.sub) chip(B("子主题", "Subtheme"), state.sub, () => { state.sub = null; });
  if (state.method) chip(B("方法", "Method"), state.method, () => { state.method = null; });
  if (state.journal) chip(B("期刊", "Journal"), state.journal, () => { state.journal = null; });
  if (state.year) chip(B("年份", "Year"), state.year, () => { state.year = null; });
  if (state.pdf === "missing") chip(B("缺少 PDF", "Missing PDF"), "", () => { state.pdf = null; });
  if (state.read) chip(state.read === "fresh" ? B("本次新增", "New papers") : B("阅读状态", "Reading"),
    state.read === "fresh" ? "" : state.read, () => { state.read = null; document.getElementById("readSelect").value = ""; });
  if (!chips.length) { bar.hidden = true; bar.innerHTML = ""; return; }
  bar.hidden = false;
  bar.innerHTML = chips.map((c, i) =>
    `<button class="fchip" type="button" data-i="${i}">${c.label}${c.value ? `: <b>${esc(c.value)}</b>` : ""}<span class="x">×</span></button>`).join("")
    + `<button class="fchip clear" type="button" id="chipClear">${B("清除全部", "Clear all")}</button>`;
  bar.querySelectorAll(".fchip[data-i]").forEach(btn => btn.addEventListener("click", () => {
    chips[Number(btn.dataset.i)].clear();
    recomputeExpansion();
    renderAll();
  }));
  document.getElementById("chipClear").addEventListener("click", clearFilters);
}

function syncHash() {
  S.writeHash({
    tab: state.tab !== "overview" ? state.tab : null,
    mode: state.mode !== "theme" ? state.mode : null,
    q: state.q || null, theme: state.theme, sub: state.sub, method: state.method,
    journal: state.journal, year: state.year, pdf: state.pdf, read: state.read, paper: activeRank,
  });
}
function setTab(tab) {
  state.tab = tab;
  document.querySelectorAll(".tab").forEach(btn => btn.classList.toggle("active", btn.dataset.tab === tab));
  document.querySelectorAll(".view").forEach(view => view.classList.toggle("active", view.id === `view-${tab}`));
}
function renderAll() {
  setTab(state.tab);
  renderOverview();
  renderFlowMap();
  renderExplore();
  renderChips();
  S.renderReadbar(document.getElementById("readbar"), papers, notes);
  syncHash();
}

function detailText(titleHtml, value) { return S.detailSection(titleHtml, value); }
function openDetail(rank) {
  const paper = papers.find(p => String(p.rank) === String(rank));
  if (!paper) return;
  const wasOpen = !!activeRank;
  activeRank = String(rank);
  navList = filteredPapers();
  let idx = navList.findIndex(p => String(p.rank) === activeRank);
  if (idx === -1) { navList = papers; idx = navList.findIndex(p => String(p.rank) === activeRank); }
  const detail = details[activeRank] || {};
  document.getElementById("detailCard").style.setProperty("--dc", colorForTheme(paperTheme(paper)));
  document.getElementById("detailEyebrow").textContent = `Rank ${paper.rank} · ${paperTheme(paper)} · ${paper.article_type || "research article"}`;
  document.getElementById("detailTitle").textContent = paper.title;
  document.getElementById("detailTags").innerHTML = [
    ["theme", paperTheme(paper)],
    ["subtheme", paperSubtheme(paper)],
    ["method", paperMethod(paper)],
  ].map(([cls, text]) => `<span class="tag ${cls}">${esc(text)}</span>`).join("")
    + (paper.local_pdf_path ? `<span class="tag pdf">PDF</span>` : "");
  const factRows = [
    [B("期刊", "Journal"), knownJournal(paper) || MISSING_JOURNAL],
    [B("日期", "Date"), paper.publication_date || "—"],
    [B("类型", "Type"), paper.article_type || "—"],
    [B("主题", "Theme"), paperTheme(paper)],
    [B("子主题", "Subtheme"), paperSubtheme(paper)],
    [B("方法", "Method"), paperMethod(paper)],
    [B("元数据", "Metadata"), paper.metadata_quality || "—"],
    [B("本地 PDF", "Local PDF"), paper.local_pdf_path ? "linked" : "missing"],
  ];
  if (S.casTier(paper)) factRows.push([B("中科院分区", "CAS Tier"), S.casLabel(paper)]);
  if (inSetCited(paper) > 0 || (paper.cited_by_count || 0) > 0) {
    factRows.push([B("被引", "Citations"), `${inSetCited(paper)} in-set · ${paper.cited_by_count || 0} global`]);
  }
  document.getElementById("detailFacts").innerHTML = factRows
    .map(([label, value]) => `<div class="detail-fact"><span>${label}</span><strong>${esc(value)}</strong></div>`).join("");
  document.getElementById("detailSections").innerHTML = [
    detailText(B("研究主题", "Research Theme"), detail.topic),
    detailText(B("方法", "Method"), detail.method),
    detailText(B("数据或案例", "Data or Case"), detail.data),
    detailText(B("主要结果", "Findings"), detail.findings),
    detailText(B("局限", "Limitations"), detail.limits),
    detailText(B("为什么重要", "Relevance"), detail.relevance),
  ].join("");
  const notesBox = document.getElementById("detailNotes");
  notesBox.innerHTML = S.notesPanelHtml(activeRank, notes.get(activeRank));
  S.bindNotesPanel(notesBox, activeRank, notes, quiet => {
    S.renderReadbar(document.getElementById("readbar"), papers, notes);
    if (!quiet) renderExplore();
  });
  document.getElementById("detailLinks").innerHTML = [
    paper.doi ? `<a class="detail-link" href="${esc(paper.doi)}" target="_blank" rel="noopener">${B("打开 DOI", "Open DOI")}</a>` : "",
    paper.local_pdf_path ? `<button class="detail-link" type="button" id="openPdfLauncher">${B("打开本地 PDF", "Open local PDF")}</button>` : "",
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
  syncHash();
}
function moveDetail(delta) {
  const idx = navList.findIndex(p => String(p.rank) === String(activeRank));
  const next = navList[idx + delta];
  if (next) openDetail(next.rank);
}

function applyHash() {
  const h = S.readHash();
  state.tab = ["overview", "explore"].includes(h.tab) ? h.tab : "overview";
  state.mode = ["theme", "method", "journal"].includes(h.mode) ? h.mode : "theme";
  state.q = h.q || "";
  state.theme = h.theme || null;
  state.sub = h.sub || null;
  state.method = h.method || null;
  state.journal = h.journal || null;
  state.year = h.year || null;
  state.pdf = h.pdf === "missing" ? "missing" : null;
  state.read = ["unread", "reading", "read", "starred", "fresh"].includes(h.read) ? h.read : null;
  document.getElementById("searchInput").value = state.q;
  document.getElementById("readSelect").value = state.read || "";
  recomputeExpansion();
  renderAll();
  if (h.paper) openDetail(h.paper); else closeDetail();
}

document.getElementById("dashTitle").textContent = spec.title || "Zotero Literature Library";
document.getElementById("dashSubtitle").textContent = spec.subtitle || "";
S.countUp(document.getElementById("paperCount"), papers.length);
S.countUp(document.getElementById("themeCount"), themeDefs.length);
S.countUp(document.getElementById("subthemeCount"), countBy(papers, paperSubtheme).length);
S.countUp(document.getElementById("methodCount"), countBy(papers, paperMethod).length);
S.countUp(document.getElementById("journalCount"), countBy(papers.filter(knownJournal), knownJournal).length);
const pdfBacked = papers.filter(p => p.local_pdf_path).length;
document.getElementById("pdfCount").textContent = `${pdfBacked}/${papers.length}`;
if (pdfBacked < papers.length) {
  const kpiPdf = document.getElementById("kpiPdf");
  kpiPdf.setAttribute("role", "button");
  kpiPdf.setAttribute("tabindex", "0");
  kpiPdf.title = "查看缺少 PDF 的文献 / Show papers missing a local PDF";
  const toggle = () => { state.pdf = state.pdf === "missing" ? null : "missing"; state.tab = "explore"; recomputeExpansion(); renderAll(); };
  kpiPdf.addEventListener("click", toggle);
  kpiPdf.addEventListener("keydown", e => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); toggle(); } });
}
if ((data.new_count || 0) > 0) {
  document.querySelector("#kpiPapers .note").insertAdjacentHTML("beforeend",
    ` <span class="tag new" title="本次构建新增 / added in this build">+${data.new_count} NEW</span>`);
}
S.initTheme(document.getElementById("themeToggle"));
S.initLang(document.getElementById("langToggle"));
S.bindSlashFocus(document.getElementById("searchInput"));

function shareCardConfig() {
  const themeCounts = new Map();
  papers.forEach(p => themeCounts.set(paperTheme(p), (themeCounts.get(paperTheme(p)) || 0) + 1));
  const themes = themeDefs
    .map(d => ({ name: d.name, count: themeCounts.get(d.name) || 0, hex: S.resolveHexLight(d.color) }))
    .filter(t => t.count > 0)
    .sort((a, b) => b.count - a.count);
  const journalMap = new Map();
  papers.forEach(p => {
    const j = knownJournal(p);
    if (!j) return;
    if (!journalMap.has(j)) journalMap.set(j, { name: j, count: 0, ifValue: 0, cas: "" });
    const row = journalMap.get(j);
    row.count += 1;
    row.ifValue = Math.max(row.ifValue, Number(p.official_impact_factor) || 0);
    if (!row.cas) row.cas = S.casLabel(p);
  });
  const journals = [...journalMap.values()]
    .sort((a, b) => b.count - a.count || b.ifValue - a.ifValue)
    .slice(0, 3)
    .map(r => ({ name: r.name, count: r.count, if: r.ifValue ? r.ifValue.toFixed(1) : "", cas: r.cas }));
  return { title: spec.title || "Zotero Library", papers: papers.length, themes, journals,
    read: notes.counts(papers), newCount: data.new_count || 0 };
}
document.getElementById("shareCard").addEventListener("click", e => S.exportShareCard(shareCardConfig(), e.currentTarget));

document.getElementById("readSelect").addEventListener("change", e => {
  state.read = e.target.value || null;
  if (state.read && state.tab === "overview") state.tab = "explore";
  recomputeExpansion();
  renderAll();
});
document.querySelectorAll(".tab").forEach(btn => btn.addEventListener("click", () => { state.tab = btn.dataset.tab; renderAll(); }));
document.querySelectorAll("#modeSeg button").forEach(btn => btn.addEventListener("click", () => {
  if (state.mode === btn.dataset.mode) return;
  state.mode = btn.dataset.mode;
  state.theme = null; state.sub = null; state.method = null; state.journal = null;
  recomputeExpansion();
  renderAll();
}));
document.getElementById("searchInput").addEventListener("input", S.debounce(e => {
  state.q = e.target.value.trim();
  if (state.q && state.tab === "overview") state.tab = "explore";
  recomputeExpansion();
  renderAll();
}, 180));
document.getElementById("kpiPapers").addEventListener("click", clearFilters);
document.getElementById("kpiPapers").addEventListener("keydown", e => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); clearFilters(); } });
document.getElementById("expandAllGroups").addEventListener("click", () => {
  groupByCategory(filteredPapers()).forEach((items, group) => {
    const key = groupStateKey(group);
    expandedGroups.add(key);
    countBy(items, paperYear).forEach(([year]) => expandedYears.add(yearStateKey(key, year)));
  });
  renderExplore();
});
document.getElementById("collapseAllGroups").addEventListener("click", () => {
  expandedGroups.clear();
  expandedYears.clear();
  renderExplore();
});
document.getElementById("exportCsv").addEventListener("click", () => {
  S.download("literature-export.csv", S.csv(filteredPapers(), [
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
  S.download("literature-export.bib", filteredPapers().map(S.bibtex).join("\n\n") + "\n", "text/plain;charset=utf-8");
});
document.getElementById("detailClose").addEventListener("click", closeDetail);
document.getElementById("detailPrev").addEventListener("click", () => moveDetail(-1));
document.getElementById("detailNext").addEventListener("click", () => moveDetail(1));
document.getElementById("detailShell").addEventListener("click", event => { if (event.target.id === "detailShell") closeDetail(); });
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

LARGE_LIBRARY_HTML = (
    LARGE_LIBRARY_HTML
    .replace("__THEME_BOOT__", THEME_BOOT_JS)
    .replace("__SHARED_CSS__", SHARED_CSS)
    .replace("__SHARED_JS__", SHARED_JS)
)


def write_large_library_dashboard(
    *,
    output_dir: Path,
    dashboard_file: str,
    data_file: str,
    details_file: str,
    pdf_open_file: str,
    data_payload: dict[str, Any],
    details: dict[str, Any],
    inline: bool = False,
) -> None:
    write_js(output_dir / data_file, "__SLR_DASHBOARD_DATA__", data_payload)
    write_js(output_dir / details_file, "__SLR_DASHBOARD_DETAILS__", details)
    if inline:
        data_script = inline_js_tag("__SLR_DASHBOARD_DATA__", data_payload)
        details_script = inline_js_tag("__SLR_DASHBOARD_DETAILS__", details)
    else:
        data_script = f'<script src="{data_file}"></script>'
        details_script = f'<script src="{details_file}"></script>'
    (output_dir / dashboard_file).write_text(
        LARGE_LIBRARY_HTML.replace("__DATA_SCRIPT__", data_script)
        .replace("__DETAILS_SCRIPT__", details_script)
        .replace("__PDF_OPEN_FILE__", pdf_open_file),
        encoding="utf-8",
    )
    (output_dir / pdf_open_file).write_text(
        PDF_OPEN_HTML.replace("__DATA_FILE__", data_file).replace("__DASHBOARD_FILE__", dashboard_file),
        encoding="utf-8",
    )
