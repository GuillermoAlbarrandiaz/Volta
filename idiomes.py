"""Versiones en catalán (/ca/) e inglés (/en/) de la web de Volta BCN.

build.py genera primero las páginas en castellano. Este módulo toma ese HTML y crea
cada versión traducida, sustituyendo cada texto con su diccionario
(data/ca.json y data/en.json: castellano -> idioma) y cambiando los enlaces
internos por sus equivalentes en el idioma.

Para cambiar una traducción: edita data/<idioma>.json y vuelve a ejecutar build.py.
Si añades textos nuevos en castellano, al ejecutar build.py se listan los que faltan
en data/<idioma>-pendiente.json (mientras tanto se muestran en castellano).
"""
import json, re, html
from pathlib import Path

ROOT = Path(__file__).resolve().parent

LANGS = {
    'ca': {'name': 'Català', 'locale': 'ca_ES', 'label': 'Idioma', 'slugs': [
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
        ('/', '/ca/'),
    ]},
    'en': {'name': 'English', 'locale': 'en_GB', 'label': 'Language', 'slugs': [
        ('/propietarios/gestion-integral/', '/en/owners/property-management/'),
        ('/propietarios/alquiler-temporada/', '/en/owners/seasonal-rentals/'),
        ('/propietarios/alquiler-corporativo/', '/en/owners/corporate-rentals/'),
        ('/propietarios/vender/', '/en/owners/sell/'),
        ('/propietarios/valorar/', '/en/owners/valuation/'),
        ('/alquilar/', '/en/rent/'),
        ('/comprar/', '/en/buy/'),
        ('/nosotros/', '/en/about/'),
        ('/contacto/', '/en/contact/'),
        ('/opiniones/', '/en/reviews/'),
        ('/aviso-legal/', '/en/legal-notice/'),
        ('/privacidad/', '/en/privacy/'),
        ('/cookies/', '/en/cookies/'),
        ('/', '/en/'),
    ]},
}
for code, L in LANGS.items():
    f = ROOT / f'data/{code}.json'
    L['dict'] = json.loads(f.read_text(encoding='utf-8')) if f.exists() else {}

def lang_path(path, lang):
    """Ruta equivalente en `lang`, o None si la página no tiene traducción."""
    if lang == 'es':
        return path
    for es, tr_ in LANGS[lang]['slugs']:
        if es == '/':
            if path == '/':
                return tr_
        elif path.startswith(es):
            return tr_ + path[len(es):]
    return None

def ca_path(path):  # compatibilidad
    return lang_path(path, 'ca')

# ───────────────── selector de idioma y hreflang ─────────────────
def switch(path, mobile=False):
    """Marcador que finalize() sustituye por el selector ES · CA · EN."""
    return f'<!--LANGSW {int(mobile)}-->'

def _switch_html(es, lang, mobile):
    links = [('es', 'ES', 'Castellano', es or '/')] + [
        (c, c.upper(), LANGS[c]['name'], (lang_path(es, c) if es else None) or lang_path('/', c)) for c in LANGS]
    a = ''.join(f'<a href="{h}" hreflang="{c}" lang="{c}" title="{t}"{" aria-current=\"true\"" if c == lang else ""}>{l}</a>' for c, l, t, h in links)
    label = LANGS[lang]['label'] if lang in LANGS else 'Idioma'
    return f'<nav class="langs{" langs-m" if mobile else ""}" aria-label="{label}">{a}</nav>'

def finalize(doc, path, lang, site='https://www.voltabcn.com', index=True):
    """Pone el selector de idioma y las etiquetas hreflang. `path` es siempre la ruta en castellano."""
    doc = re.sub(r'<!--LANGSW (\d)-->', lambda m: _switch_html(path, lang, m.group(1) == '1'), doc)
    alts = [(c, lang_path(path, c)) for c in LANGS]
    if index and all(p for _, p in alts):
        alt = (f'<link rel="alternate" hreflang="es" href="{site}{path}">'
               + ''.join(f'<link rel="alternate" hreflang="{c}" href="{site}{p}">' for c, p in alts)
               + f'<link rel="alternate" hreflang="x-default" href="{site}{path}">\n')
        doc = doc.replace('</head>', alt + '</head>', 1)
    return doc

# ───────────────── traducción ─────────────────
class Translator:
    def __init__(self, lang, site):
        self.lang, self.site = lang, site
        self.D = LANGS[lang]['dict']
        self.missing = {}

    def tr(self, text):
        core = text.strip()
        if not core or not re.search(r'[A-Za-zÀ-ÿ]', core):
            return text
        if core in self.D:
            return text.replace(core, self.D[core], 1)
        self.missing[core] = core
        return text

    def map_url(self, u):
        site = self.site
        pre = ''
        if u.startswith(site):
            pre, u = site, u[len(site):]
        if not u.startswith('/') or u.startswith('//'):
            return pre + u
        m = re.match(r'([^#?]*)(.*)', u)
        p, rest = m.group(1), m.group(2)
        c = lang_path(p, self.lang) if p.endswith('/') else None
        return pre + (c + rest if c else u)

    def json(self, obj):
        if isinstance(obj, dict):
            return {k: (self.json(v) if k not in ('@type', '@context', '@id', 'unitCode') else v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self.json(v) for v in obj]
        if isinstance(obj, str):
            if obj.startswith(self.site) or obj.startswith('/'):
                return self.map_url(obj)
            return self.tr(obj)
        return obj

    ATTRS = ('alt', 'aria-label', 'placeholder', 'title', 'data-label', 'value')

    def attr(self, v):
        return html.escape(self.tr(html.unescape(v)), quote=True)

    def tag(self, tag):
        if tag.startswith('<!--'):
            return tag
        name = re.match(r'</?\s*([a-zA-Z0-9-]+)', tag)
        name = name.group(1).lower() if name else ''
        tag = re.sub(r'\bhref="([^"]*)"', lambda m: f'href="{self.map_url(m.group(1))}"', tag)
        for a in self.ATTRS:
            if a == 'value' and not (name == 'input' and re.search(r'type="(checkbox|radio)"', tag)):
                continue  # solo los valores que el usuario ve como opciones
            tag = re.sub(rf'(\s{a}=")([^"]*)(")', lambda m: m.group(1) + self.attr(m.group(2)) + m.group(3), tag)
        if name == 'meta':
            if re.search(r'(name="description"|property="og:(title|description)")', tag):
                tag = re.sub(r'(content=")([^"]*)(")', lambda m: m.group(1) + self.attr(m.group(2)) + m.group(3), tag)
            tag = re.sub(r'(property="og:url" content=")([^"]*)', lambda m: m.group(1) + self.map_url(m.group(2)), tag)
            tag = tag.replace('content="es_ES"', f'content="{LANGS[self.lang]["locale"]}"')
        if name == 'link' and 'rel="canonical"' in tag:
            tag = re.sub(r'(href=")([^"]*)', lambda m: m.group(1) + self.map_url(m.group(2)), tag)
        if name == 'html':
            tag = tag.replace('lang="es"', f'lang="{self.lang}"')
        return tag

    TAG = re.compile(r'(<!--.*?-->|<[^>]+>)', re.S)

    def doc(self, doc):
        parts = self.TAG.split(doc)
        script = None
        for i, part in enumerate(parts):
            if not part:
                continue
            if part.startswith('<'):
                low = part.lower()
                if low.startswith('<script'):
                    script = 'json' if ('application/ld+json' in low or 'application/json' in low) else 'js'
                elif low.startswith('</script') or low.startswith('</style'):
                    script = None
                elif low.startswith('<style'):
                    script = 'css'
                parts[i] = self.tag(part)
            elif script == 'json':
                parts[i] = json.dumps(self.json(json.loads(part)), ensure_ascii=False)
            elif script is None:
                parts[i] = self.tr(part)
        return ''.join(parts)

def build_lang(lang, raw, root, site):
    """Escribe las páginas traducidas y devuelve las rutas indexables para el sitemap."""
    t = Translator(lang, site)
    out_paths = []
    for path, (doc, index) in raw.items():
        target = lang_path(path, lang)
        if not target:
            continue
        d = finalize(t.doc(doc), path, lang, site, index)
        out = root / target.lstrip('/') / 'index.html'
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(d, encoding='utf-8')
        if index:
            out_paths.append(target)
    pend = root / f'data/{lang}-pendiente.json'
    if t.missing:
        pend.write_text(json.dumps(sorted(t.missing), ensure_ascii=False, indent=1), encoding='utf-8')
        print(f'{LANGS[lang]["name"]}: {len(t.missing)} textos sin traducir (ver data/{lang}-pendiente.json).')
    elif pend.exists():
        pend.unlink()
    return out_paths

def build_all(raw, root, site):
    paths = []
    for lang in LANGS:
        paths += build_lang(lang, raw, root, site)
    return paths
