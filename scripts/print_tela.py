#!/usr/bin/env python3
"""Captura de tela com Playwright (usa o Google Chrome instalado na máquina).
Executar com: scripts/.venv-tools/bin/python scripts/print_tela.py ...

uso: scripts/print_tela.py <url> <saida.png> [--cookie nome=valor] [--full]
Se a página disparar um diálogo JS (alert/confirm), a mensagem é impressa em
stdout como "DIALOG: <tipo> <mensagem>" — prova de execução de script (XSS).
O print é tirado com o diálogo aceito (headless não desenha alertas nativos).
"""
import argparse
import sys
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

ap = argparse.ArgumentParser()
ap.add_argument("url"); ap.add_argument("saida")
ap.add_argument("--cookie", action="append", default=[])
ap.add_argument("--full", action="store_true")
a = ap.parse_args()

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True)
    ctx = browser.new_context(viewport={"width": 1280, "height": 800})
    host = urlparse(a.url).hostname
    for c in a.cookie:
        k, v = c.split("=", 1)
        ctx.add_cookies([{"name": k, "value": v, "domain": host, "path": "/"}])
    page = ctx.new_page()
    dialogs = []

    def on_dialog(d):
        dialogs.append((d.type, d.message))
        print(f"DIALOG: {d.type} {d.message}")
        d.accept()

    page.on("dialog", on_dialog)
    resp = page.goto(a.url, wait_until="networkidle")
    page.wait_for_timeout(800)
    # Banner com o status HTTP (verde 2xx / vermelho 4xx-5xx) — deixa o print
    # autoexplicativo, principalmente para respostas de erro JSON (401/403/404).
    if resp is not None:
        cor = "#2e7d32" if resp.status < 400 else "#c62828"
        page.evaluate(
            """(o) => { const b = document.createElement('div');
              b.textContent = 'HTTP ' + o.s + '  ·  ' + o.u;
              b.style.cssText = 'position:fixed;top:0;left:0;right:0;background:'+o.c+
                ';color:#fff;padding:10px 14px;font:bold 16px ui-monospace,monospace;z-index:99999';
              document.body.style.marginTop='48px'; document.body.prepend(b); }""",
            {"s": resp.status, "u": a.url, "c": cor},
        )
    if dialogs:
        # Banner injetado SÓ no print (não altera o HTML servido) para registrar o alert.
        page.evaluate("""m => { const b = document.createElement('div');
          b.textContent = '⚠ alert() executado pela página: ' + m;
          b.style.cssText = 'position:fixed;top:0;left:0;right:0;background:#c00;color:#fff;padding:8px;font:bold 16px sans-serif;z-index:99999';
          document.body.appendChild(b); }""", " | ".join(m for _, m in dialogs))
    page.screenshot(path=a.saida, full_page=a.full)
    print(f"HTTP {resp.status if resp else '?'} {a.url} -> {a.saida}; dialogs={len(dialogs)}")
    browser.close()
sys.exit(0)
