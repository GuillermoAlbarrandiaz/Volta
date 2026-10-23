"""Versión en catalán de la web de Volta BCN.

build.py genera primero las páginas en castellano. Este módulo toma ese HTML y crea
la versión catalana en /ca/, traduciendo cada texto con el diccionario data/ca.json
(castellano -> catalán) y cambiando los enlaces internos por sus equivalentes en /ca/.

Para cambiar una traducción: edita data/ca.json y vuelve a ejecutar build.py.
Si añades textos nuevos en castellano, al ejecutar build.py se listan los que faltan
por traducir en data/ca-pendiente.json (mientras tanto se muestran en castellano).
"""
import json, re, html
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CA_FILE = ROOT / 'data/ca.json'
CA = json.loads(CA_FILE.read_text(encoding='utf-8')) if CA_FILE.exists() else {}

# Rutas en castellano -> rutas en catalán (las fichas de inmuebles conservan su identificador)
SLUGS = [
    ('/propietarios/gestion-integral/', '/ca/propietaris/gestio-integral/'),
    ('/propietarios/alquiler-temporada/', '/ca/propietaris/lloguer-temporada/'),
    ('/propietarios/alquiler-corporativo/', '/ca/propietaris/lloguer-corporatiu/'),
    ('/propietarios/vender/', '/ca/propietaris/vendre/'),
    ('/propietarios/valorar/', '/ca/propietaris/valorar/'),
    ('/alquilar/', '/ca/llogar/'),
    ('/comprar/', '/ca/comprar/'),
    ('/nosotros/', '/ca/nosaltres/'),
    ('/contacto/', '/ca/contacte/'),
    ('/opiniones/', '/ca/opinions/'),
    ('/aviso-legal/', '/ca/avis-legal/'),
    ('/privacidad/', '/ca/privacitat/'),
    ('/cookies/', '/ca/galetes/'),
]

def ca_path(path):
    """Ruta catalana equivalente, o None si la página no tiene versión catalana."""
    if path == '/':
        return '/ca/'
    for es, ca in SLUGS:
        if path.startswith(es):
            return ca + path[len(es):]
    return None

def es_path(path):
    if path in ('/ca/', '/ca'):
        return '/'
    for es, ca in SLUGS:
        if path.startswith(ca):
            return es + path[len(ca):]
    return path

# ───────────────── selector de idioma y hreflang ─────────────────
def switch(path, mobile=False):
    """Marcador que finalize() sustituye por el selector ES · CA · EN."""
    return f'<!--LANGSW {int(mobile)}-->'

def _switch_html(es, lang, mobile):
    ca = ca_path(es) if es else None
    links = [('es', 'ES', 'Castellano', es or '/'), ('ca', 'CA', 'Català', ca or '/ca/'), ('en', 'EN', 'English', '/en/')]
    a = ''.join(f'<a href="{h}" hreflang="{c}" lang="{c}" title="{t}"{" aria-current=\"true\"" if c == lang else ""}>{l}</a>' for c, l, t, h in links)
    label = {'es': 'Idioma', 'ca': 'Idioma', 'en': 'Language'}[lang]
    return f'<nav class="langs{" langs-m" if mobile else ""}" aria-label="{label}">{a}</nav>'

def finalize(doc, path, lang, site='https://www.voltabcn.com', index=True):
    """Pone el selector de idioma y las etiquetas hreflang. `path` es siempre la ruta en castellano."""
    es = path if lang in ('es', 'ca') else None
    doc = re.sub(r'<!--LANGSW (\d)-->', lambda m: _switch_html(es, lang, m.group(1) == '1'), doc)
    ca = ca_path(path) if es else None
    if ca and index:
        alt = (f'<link rel="alternate" hreflang="es" href="{site}{path}">'
               f'<link rel="alternate" hreflang="ca" href="{site}{ca}">'
               f'<link rel="alternate" hreflang="x-default" href="{site}{path}">\n')
        doc = doc.replace('</head>', alt + '</head>', 1)
    return doc

# ───────────────── traducción ─────────────────
MISSING = {}

def tr(text):
    """Traduce un texto conservando los espacios de alrededor."""
    core = text.strip()
    if not core or not re.search(r'[A-Za-zÀ-ÿ]', core):
        return text
    if core in CA:
        return text.replace(core, CA[core], 1)
    MISSING[core] = core
    return text

def map_url(u, site):
    pre = ''
    if u.startswith(site):
        pre, u = site, u[len(site):]
    if not u.startswith('/') or u.startswith('//'):
        return pre + u
    m = re.match(r'([^#?]*)(.*)', u)
    p, rest = m.group(1), m.group(2)
    c = ca_path(p) if p.endswith('/') else None
    return pre + (c + rest if c else u)

def _tr_json(obj, site):
    if isinstance(obj, dict):
        return {k: (_tr_json(v, site) if k not in ('@type', '@context', '@id', 'unitCode') else v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_tr_json(v, site) for v in obj]
    if isinstance(obj, str):
        if obj.startswith(site) or obj.startswith('/'):
            return map_url(obj, site)
        return tr(obj)
    return obj

ATTRS = ('alt', 'aria-label', 'placeholder', 'title', 'data-label', 'value')
TAG = re.compile(r'(<!--.*?-->|<[^>]+>)', re.S)

def _tr_attr(v):
    return html.escape(tr(html.unescape(v)), quote=True)

def _tr_tag(tag, site):
    if tag.startswith('<!--'):
        return tag
    name = re.match(r'</?\s*([a-zA-Z0-9-]+)', tag)
    name = name.group(1).lower() if name else ''
    tag = re.sub(r'\bhref="([^"]*)"', lambda m: f'href="{map_url(m.group(1), site)}"', tag)
    for a in ATTRS:
        if a == 'value' and not (name == 'input' and re.search(r'type="(checkbox|radio)"', tag)):
            continue  # solo los valores que el usuario ve como opciones
        tag = re.sub(rf'(\s{a}=")([^"]*)(")', lambda m: m.group(1) + _tr_attr(m.group(2)) + m.group(3), tag)
    if name == 'meta':
        if re.search(r'(name="description"|property="og:(title|description)")', tag):
            tag = re.sub(r'(content=")([^"]*)(")', lambda m: m.group(1) + html.escape(tr(html.unescape(m.group(2))), quote=True) + m.group(3), tag)
        tag = re.sub(r'(property="og:url" content=")([^"]*)', lambda m: m.group(1) + map_url(m.group(2), site), tag)
        tag = tag.replace('content="es_ES"', 'content="ca_ES"')
    if name == 'link' and 'rel="canonical"' in tag:
        tag = re.sub(r'(href=")([^"]*)', lambda m: m.group(1) + map_url(m.group(2), site), tag)
    if name == 'html':
        tag = tag.replace('lang="es"', 'lang="ca"')
    return tag

def translate(doc, site):
    parts = TAG.split(doc)
    script = None
    for i, part in enumerate(parts):
        if not part:
            continue
        if part.startswith('<'):
            low = part.lower()
            if low.startswith('<script'):
                script = 'json' if ('application/ld+json' in low or 'application/json' in low) else 'js'
            elif low.startswith('</script'):
                script = None
            elif low.startswith('<style'):
                script = 'css'
            elif low.startswith('</style'):
                script = None
            parts[i] = _tr_tag(part, site)
        elif script == 'json':
            parts[i] = json.dumps(_tr_json(json.loads(part), site), ensure_ascii=False)
        elif script is None:
            parts[i] = tr(part)
    return ''.join(parts)

def build_ca(raw, root, site):
    """Escribe las páginas en /ca/ y devuelve las rutas indexables para el sitemap."""
    import silabas
    out_paths = []
    for path, (doc, index) in raw.items():
        ca = ca_path(path)
        if not ca:
            continue
        d = translate(doc, site)
        d = finalize(d, path, 'ca', site, index)
        d = silabas.html(d) if getattr(silabas, 'CA_OK', False) else d
        out = root / ca.lstrip('/') / 'index.html'
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(d, encoding='utf-8')
        if index:
            out_paths.append(ca)
    pend = root / 'data/ca-pendiente.json'
    if MISSING:
        pend.write_text(json.dumps(sorted(MISSING), ensure_ascii=False, indent=1), encoding='utf-8')
        print(f'Catalán: {len(MISSING)} textos sin traducir (ver data/ca-pendiente.json).')
    elif pend.exists():
        pend.unlink()
    return out_paths
