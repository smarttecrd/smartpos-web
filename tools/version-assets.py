#!/usr/bin/env python3
"""Versiona los assets locales con ?v=<hash del contenido> para romper la cache.

Uso (desde la raiz del sitio):  python tools/version-assets.py
Es idempotente: solo cambia un ?v= cuando el contenido del archivo cambio.
Reescribe href/src/url() en los .html y style.css, y los "src" de manifest.webmanifest.
"""
import hashlib, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
# Primero los archivos que otros referencian (manifest, css) para que los hashes de las paginas salgan estables.
PAGES = [ROOT / "manifest.webmanifest", ROOT / "style.css"] + sorted(ROOT.glob("*.html"))
LOCAL = r"/?(?:assets/[^\"')?#\s]+|style\.css|favicon\.ico|manifest\.webmanifest)"
PAT = re.compile(r'(?P<pre>(?:href|src)=["\']|url\(["\']?|"src":\s*")(?P<path>' + LOCAL + r')(?:\?v=[0-9a-f]+)?(?P<frag>#[^"\')\s]*)?')

def digest(rel: str) -> str | None:
    f = ROOT / rel.lstrip("/")
    return hashlib.sha1(f.read_bytes()).hexdigest()[:8] if f.is_file() else None

def fix(m):
    h = digest(m.group("path"))
    if not h:
        print("  aviso: no existe", m.group("path"), file=sys.stderr)
        return m.group(0)
    return f'{m.group("pre")}{m.group("path")}?v={h}{m.group("frag") or ""}'

changed = 0
for page in PAGES:
    if not page.is_file():
        continue
    old = page.read_text(encoding="utf-8")
    new = PAT.sub(fix, old)
    if new != old:
        page.write_text(new, encoding="utf-8")
        changed += 1
        print("versionado:", page.name)
print("listo;", changed, "archivo(s) actualizado(s)")
