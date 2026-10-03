#!/usr/bin/env python3
"""Renderiza um .mmd em PNG usando o Chrome local (Playwright) + mermaid.js (jsDelivr).

uso (requer `pip install playwright`): python scripts/render_mermaid.py docs/img/dfd.mmd docs/img/dfd.png
"""
import html
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

src, out = Path(sys.argv[1]), sys.argv[2]
page_html = f"""<!doctype html><html><head><meta charset="utf-8">
<script src="https://cdn.jsdelivr.net/npm/mermaid@10.9.1/dist/mermaid.min.js"></script></head>
<body style="background:#fff;margin:16px"><pre class="mermaid">{html.escape(src.read_text())}</pre>
<script>mermaid.initialize({{startOnLoad:true, securityLevel:'strict', flowchart:{{htmlLabels:true}}}});</script>
</body></html>"""
with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome", headless=True)
    pg = b.new_page(viewport={"width": 1900, "height": 1200}, device_scale_factor=2)
    pg.set_content(page_html, wait_until="networkidle")
    pg.wait_for_selector("pre.mermaid svg", timeout=20000)
    pg.locator("pre.mermaid svg").screenshot(path=out)
    b.close()
print("ok ->", out)
