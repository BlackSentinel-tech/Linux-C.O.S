#!/usr/bin/env python3
"""Render the Linux-C.O.S website: website/_src/pages/*.html -> website/*.html.

Every page shares one header (with the navigation menu), one footer and one
<head>, so they live here once instead of being copy-pasted into 7 files.
The output is plain static HTML (works without JS, on GitHub Pages, or
straight from a file server) and is committed, so publishing needs no build.

Each source page starts with a metadata comment:

    <!--
    title_en: Features
    title_es: Características
    desc_en: ...
    desc_es: ...
    nav: features            (which menu item is the current page)
    scripts: tools.js        (optional, extra scripts from assets/js/)
    -->

    python3 scripts/build-website.py          # rebuild
    python3 scripts/build-website.py --check  # exit 1 if output is stale (CI)
"""
from __future__ import annotations

import base64
import hashlib
import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "website"
SRC = SITE / "_src/pages"
REPO = "https://github.com/BlackSentinel-tech/Linux-C.O.S"
SITE_NAME = "Linux-C.O.S"

NAV = [  # (key, href, en, es)
    ("features", "features.html", "Features", "Características"),
    ("tools", "tools.html", "Tools", "Herramientas"),
    ("download", "download.html", "Download", "Descargar"),
    ("docs", "docs.html", "Docs", "Documentación"),
    ("faq", "faq.html", "FAQ", "Preguntas"),
]

# Runs before first paint so there is no flash of the wrong language/theme.
BOOT_JS = (
    "(function(){var d=document.documentElement,l,t;"
    "try{l=localStorage.getItem('cos-lang');t=localStorage.getItem('cos-theme')}catch(e){}"
    "if(l!=='es'&&l!=='en'){l=((navigator.languages&&navigator.languages[0])||navigator.language||'en')"
    ".toLowerCase().indexOf('es')===0?'es':'en'}"
    "d.setAttribute('data-lang',l);d.lang=l;"
    "if(t==='light'||t==='dark')d.setAttribute('data-theme',t)})();"
)
BOOT_HASH = base64.b64encode(hashlib.sha256(BOOT_JS.encode()).digest()).decode()

CSP = (
    "default-src 'self'; "
    f"script-src 'self' 'sha256-{BOOT_HASH}'; "
    "style-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'self'; "
    "object-src 'none'; base-uri 'none'; form-action 'none'"
)

ICONS = {
    "menu": '<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path class="l1" d="M4 7h16"/><path class="l2" d="M4 12h16"/><path class="l3" d="M4 17h16"/></svg>',
    "sun": '<svg class="i-sun" viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>',
    "moon": '<svg class="i-moon" viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg>',
    "github": '<svg viewBox="0 0 24 24" aria-hidden="true" fill="currentColor"><path d="M12 .5a11.5 11.5 0 0 0-3.6 22.4c.6.1.8-.3.8-.6v-2c-3.2.7-3.9-1.5-3.9-1.5-.5-1.3-1.3-1.7-1.3-1.7-1-.7.1-.7.1-.7 1.2.1 1.8 1.2 1.8 1.2 1 1.8 2.8 1.3 3.5 1 .1-.8.4-1.3.7-1.6-2.6-.3-5.3-1.3-5.3-5.7 0-1.3.5-2.3 1.2-3.1-.1-.3-.5-1.5.1-3.1 0 0 1-.3 3.2 1.2a11 11 0 0 1 5.8 0c2.2-1.5 3.2-1.2 3.2-1.2.6 1.6.2 2.8.1 3.1.8.8 1.2 1.9 1.2 3.1 0 4.4-2.7 5.4-5.3 5.7.4.4.8 1.1.8 2.2v3.3c0 .3.2.7.8.6A11.5 11.5 0 0 0 12 .5z"/></svg>',
    "up": '<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 19V5M5 12l7-7 7 7"/></svg>',
}


def bi(en: str, es: str) -> str:
    """Bilingual inline text: both spans ship, CSS shows the active one."""
    return f'<span data-l="en">{en}</span><span data-l="es">{es}</span>'


def parse(path: Path) -> tuple[dict[str, str], str]:
    text = path.read_text()
    m = re.match(r"\s*<!--(.*?)-->\s*", text, re.S)
    if not m:
        raise SystemExit(f"{path}: missing metadata comment")
    meta: dict[str, str] = {}
    for line in m.group(1).strip().splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    for key in ("title_en", "title_es", "desc_en", "desc_es"):
        if key not in meta:
            raise SystemExit(f"{path}: metadata is missing '{key}'")
    return meta, text[m.end():]


def header(current: str) -> str:
    items = []
    for key, href, en, es in NAV:
        cur = ' aria-current="page"' if key == current else ""
        items.append(f'<li><a href="{href}"{cur}>{bi(en, es)}</a></li>')
    home_cur = ' aria-current="page"' if current == "home" else ""
    items.insert(0, f'<li class="mobile-only"><a href="index.html"{home_cur}>{bi("Home", "Inicio")}</a></li>')
    items.append(f'<li class="mobile-only"><a href="{REPO}" rel="noopener">GitHub</a></li>')
    return f"""<a class="skip-link" href="#main">{bi("Skip to content", "Saltar al contenido")}</a>
<header class="site-header">
  <nav class="nav container" aria-label="Main" data-aria-en="Main" data-aria-es="Principal">
    <a class="brand" href="index.html"{home_cur}><img src="assets/img/logo.svg" alt="Linux-C.O.S" width="30" height="30"><span aria-hidden="true">LINUX-C.O.S</span></a>
    <ul class="nav-links" id="primary-nav">
      {"".join(items)}
    </ul>
    <div class="nav-tools">
      <a class="icon-btn nav-gh" href="{REPO}" rel="noopener" aria-label="Linux-C.O.S on GitHub" data-aria-en="Linux-C.O.S on GitHub" data-aria-es="Linux-C.O.S en GitHub">{ICONS["github"]}</a>
      <button class="icon-btn" id="lang-toggle" type="button"><span data-l="en" lang="es">ES<span class="visually-hidden">, español</span></span><span data-l="es" lang="en">EN<span class="visually-hidden">, English</span></span></button>
      <button class="icon-btn" id="theme-toggle" type="button" aria-pressed="false">{ICONS["sun"]}{ICONS["moon"]}<span class="visually-hidden">{bi("Light theme", "Tema claro")}</span></button>
      <button class="icon-btn menu-toggle" id="menu-toggle" type="button" aria-controls="primary-nav" aria-expanded="false" aria-label="Open menu">{ICONS["menu"]}</button>
    </div>
  </nav>
</header>"""


def footer() -> str:
    return f"""<footer class="site-footer">
  <div class="container">
    <div class="footer-grid">
      <div>
        <a class="brand" href="index.html"><img src="assets/img/logo.svg" alt="Linux-C.O.S" width="30" height="30"><span aria-hidden="true">LINUX-C.O.S</span></a>
        <p>{bi("Cyber Offensive &amp; defensive Security. A Kali-based distribution with Parrot and BlackArch tools, a blue-team stack and hardening on by default.",
               "Cyber Offensive &amp; defensive Security. Una distribución basada en Kali con herramientas de Parrot y BlackArch, stack blue-team y hardening activado por defecto.")}</p>
        <p>{bi("This site makes no third-party requests and sets no cookies.", "Este sitio no hace peticiones a terceros ni usa cookies.")}</p>
      </div>
      <div>
        <h2>{bi("Product", "Producto")}</h2>
        <ul>
          <li><a href="features.html">{bi("Features", "Características")}</a></li>
          <li><a href="tools.html">{bi("Tool catalog", "Catálogo de herramientas")}</a></li>
          <li><a href="download.html">{bi("Download &amp; build", "Descarga y compilación")}</a></li>
        </ul>
      </div>
      <div>
        <h2>{bi("Help", "Ayuda")}</h2>
        <ul>
          <li><a href="docs.html">{bi("Documentation", "Documentación")}</a></li>
          <li><a href="faq.html">{bi("FAQ", "Preguntas frecuentes")}</a></li>
          <li><a href="{REPO}/issues" rel="noopener">{bi("Report a bug", "Reportar un error")}</a></li>
        </ul>
      </div>
      <div>
        <h2>{bi("Project", "Proyecto")}</h2>
        <ul>
          <li><a href="{REPO}" rel="noopener">{bi("Source code", "Código fuente")}</a></li>
          <li><a href="{REPO}/blob/main/build/README.md" rel="noopener">{bi("Build notes", "Notas de compilación")}</a></li>
          <li><a href="{REPO}/releases" rel="noopener">{bi("Releases", "Versiones")}</a></li>
        </ul>
      </div>
    </div>
    <div class="footer-bottom">
      <span>© <span id="year">2026</span> {bi("Linux-C.O.S project", "Proyecto Linux-C.O.S")} · v0.1 “Génesis”</span>
      <span>{bi("Kali, Parrot and BlackArch are trademarks of their respective owners; Linux-C.O.S is not affiliated with them.",
               "Kali, Parrot y BlackArch son marcas de sus respectivos dueños; Linux-C.O.S no está afiliado a ellos.")}</span>
    </div>
  </div>
</footer>
<button class="icon-btn to-top" type="button" aria-label="Back to top">{ICONS["up"]}</button>"""


def render(path: Path) -> str:
    meta, body = parse(path)
    page = path.stem
    scripts = ["site.js"] + [s.strip() for s in meta.get("scripts", "").split(",") if s.strip()]
    script_tags = "\n".join(
        f'<script src="{s if s.startswith("assets/") else "assets/js/" + s}" defer></script>' for s in scripts)
    e = html.escape
    full_en = meta["title_en"] if page == "index" else f'{meta["title_en"]} · {SITE_NAME}'
    full_es = meta["title_es"] if page == "index" else f'{meta["title_es"]} · {SITE_NAME}'
    body = body.replace("{{REPO}}", REPO)
    return f"""<!doctype html>
<html lang="en" data-title-en="{e(full_en)}" data-title-es="{e(full_es)}" data-desc-en="{e(meta['desc_en'])}" data-desc-es="{e(meta['desc_es'])}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="{CSP}">
<meta name="referrer" content="no-referrer">
<title>{e(full_en)}</title>
<meta name="description" content="{e(meta['desc_en'])}">
<meta name="theme-color" content="#070a14">
<meta property="og:title" content="{e(full_en)}">
<meta property="og:description" content="{e(meta['desc_en'])}">
<meta property="og:type" content="website">
<meta property="og:image" content="assets/img/og.png">
<link rel="icon" href="assets/img/logo.svg" type="image/svg+xml">
<link rel="icon" href="assets/img/favicon-32.png" sizes="32x32" type="image/png">
<link rel="apple-touch-icon" href="assets/img/apple-touch-icon.png">
<script>{BOOT_JS}</script>
<link rel="stylesheet" href="assets/css/site.css">
{script_tags}
</head>
<body>
{header(meta.get("nav", page))}
<main id="main" tabindex="-1">
{body.strip()}
</main>
{footer()}
</body>
</html>
"""


def with_base(text: str, base: str) -> str:
    """Make relative href/src absolute under `base` (used for 404.html)."""
    return re.sub(r'(href|src)="(?![a-z]+:|/|#|data:)([^"]*)"',
                  lambda m: f'{m.group(1)}="{base}{m.group(2)}"', text)


def main() -> int:
    # --base /Linux-C.O.S/ : what the Pages workflow passes, from
    # actions/configure-pages; only 404.html needs it
    base = ""
    if "--base" in sys.argv:
        base = sys.argv[sys.argv.index("--base") + 1].rstrip("/") + "/"
    pages = sorted(SRC.glob("*.html"))
    if not pages:
        raise SystemExit(f"no pages in {SRC}")
    stale = []
    for p in pages:
        out = SITE / p.name
        text = render(p)
        if base and p.stem == "404":
            text = with_base(text, base)
        if "--check" in sys.argv[1:]:
            if not out.exists() or out.read_text() != text:
                stale.append(out.name)
        else:
            out.write_text(text)
    if "--check" in sys.argv[1:]:
        if stale:
            print("website pages are stale: " + ", ".join(stale) + " -- run: python3 scripts/build-website.py")
            return 1
        print(f"website pages are in sync ({len(pages)})")
        return 0
    print(f"built {len(pages)} pages into {SITE.relative_to(ROOT)}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
