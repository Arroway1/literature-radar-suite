# Examples / 示例

`demo-review/` 是一份**合成**的 21 篇演示数据（标题、作者、期刊均为虚构，用于预览仪表盘效果）。

安装后两分钟看到效果 / See the dashboard in two minutes:

```bash
python scripts/build_literature_dashboard.py build   --papers examples/demo-review/metadata/papers.json   --spec examples/demo-review/dashboard-spec.json   --output-dir examples/demo-review --dashboard-name demo-dashboard --inline --no-snapshot
```

然后双击打开 `examples/demo-review/demo-dashboard.html`。
Then open `examples/demo-review/demo-dashboard.html` in a browser.

要生成你自己的仪表盘，请按 SKILL.md / README 的 Zotero 直读模式或关键词检索模式运行。
To build your own dashboard, follow the Zotero direct-import or keyword-search workflow in SKILL.md / README.
