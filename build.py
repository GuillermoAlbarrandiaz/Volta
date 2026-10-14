#!/usr/bin/env python3
"""Genera la web estática de Volta BCN a partir de data/inmuebles.json y data/testimonios.json.

Uso:  python3 build.py   (escribe las páginas en esta misma carpeta)
Para añadir, editar o retirar un inmueble basta con modificar data/inmuebles.json
y poner sus fotos en inmuebles/<carpeta>/01.jpg, 02.jpg…  Después se vuelve a ejecutar.
"""
import json, os, re, html, datetime
import silabas
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SITE = 'https://www.voltabcn.com'
TEL = '+34 647 224 442'
TEL_LINK = 'tel:+34647224442'
WA_LINK = 'https://wa.me/34647224442'
EMAIL = 'info@voltabcn.com'
YEAR = datetime.date.today().year

E = lambda s: html.escape(str(s), quote=True)
PROPS = json.load(open(ROOT / 'data/inmuebles.json', encoding='utf-8'))
TESTI = json.load(open(ROOT / 'data/testimonios.json', encoding='utf-8'))
PAGES = []  # para el sitemap

def url_of(p):
    return f"/{'alquilar' if p['operacion'] == 'alquiler' else 'comprar'}/{p['id']}/"

def foto(p, n=1, thumb=False):
    if p.get('sin_miniaturas'): thumb = False
    return f"/inmuebles/{p['carpeta']}/{'t/' if thumb else ''}{n:02d}.jpg"

# ───────────────────────── plantilla común ─────────────────────────
NAV = [('Comprar', '/comprar/'), ('Alquilar', '/alquilar/')]
OWN = [('Gestión integral de alquileres', 'Nos ocupamos del día a día', '/propietarios/gestion-integral/'),
       ('Vende tu propiedad', 'Comercialización y venta', '/propietarios/vender/'),
       ('Valora tu inmueble', 'Estimación orientativa', '/propietarios/valorar/')]

def header(path, overlay=False):
    def cur(href): return ' aria-current="page"' if path.startswith(href) else ''
    own_cur = ' is-current' if path.startswith('/propietarios/') else ''
    own = ''.join(f'<a href="{h}"><b>{t}</b><small>{s}</small></a>' for t, s, h in OWN)
    links = ''.join(f'<a href="{h}"{cur(h)}>{t}</a>' for t, h in NAV)
    return f'''<a class="skip" href="#main">Saltar al contenido</a>
<header class="site-header{' overlay' if overlay else ''}">
  <div class="wrap bar">
    <a class="logo" href="/" aria-label="Volta, inicio">VOLT<span>A</span></a>
    <nav class="nav" aria-label="Principal">
      {links}
      <div class="dd{own_cur}"><button type="button" aria-expanded="false" aria-haspopup="true">Propietarios <i></i></button>
        <div class="dd-panel">{own}</div></div>
      <a href="/nosotros/"{cur('/nosotros/')}>Nosotros</a>
      <a href="/contacto/"{cur('/contacto/')}>Contacto</a>
    </nav>
    <a class="header-cta" href="{TEL_LINK}">{TEL}</a>
    <button class="burger" type="button" aria-label="Abrir menú" aria-expanded="false" aria-controls="mnav"><span></span></button>
  </div>
</header>
<div class="mnav" id="mnav" aria-hidden="true">
  <button class="mnav-close" type="button" aria-label="Cerrar menú">×</button>
  <a href="/">Inicio</a><a href="/comprar/">Comprar</a><a href="/alquilar/">Alquilar</a>
  <div class="sub"><p>Propietarios</p>{''.join(f'<a href="{h}">{t}</a>' for t, s, h in OWN)}</div>
  <a href="/nosotros/">Nosotros</a><a href="/contacto/">Contacto</a>
  <div class="contact"><a href="{TEL_LINK}">{TEL}</a><a href="mailto:{EMAIL}">{EMAIL}</a><a href="{WA_LINK}" rel="noopener" target="_blank">WhatsApp</a></div>
</div>'''

def footer():
    return f'''<footer class="site-footer">
  <div class="wrap">
    <div class="foot">
      <div><a class="logo" href="/">VOLT<span style="color:var(--orange)">A</span></a>
        <p>Gestión integral, alquiler y compraventa de viviendas en Barcelona.</p>
        <p><a href="mailto:{EMAIL}">{EMAIL}</a><br><a href="{TEL_LINK}">{TEL}</a></p></div>
      <div><h4>Inmuebles</h4><ul><li><a href="/alquilar/">Alquilar</a></li><li><a href="/comprar/">Comprar</a></li></ul></div>
      <div><h4>Propietarios</h4><ul>{''.join(f'<li><a href="{h}">{t}</a></li>' for t, s, h in OWN)}</ul></div>
      <div><h4>Volta</h4><ul><li><a href="/nosotros/">Nosotros</a></li><li><a href="/opiniones/">Opiniones</a></li><li><a href="/contacto/">Contacto</a></li></ul></div>
    </div>
    <div class="foot-bottom"><span>© {YEAR} Volta BCN · Barcelona</span>
      <nav aria-label="Legal"><a href="/aviso-legal/">Aviso legal</a><a href="/privacidad/">Política de privacidad</a><a href="/cookies/">Política de cookies</a></nav></div>
  </div>
</footer>'''

def sin_punto(doc):
    """Quita el punto final de los títulos (h1/h2/h3) de menos de 7 palabras."""
    def fix(m):
        inner = m.group(2)
        txt = re.sub(r'<[^>]+>', '', inner).strip()
        if txt.endswith('.') and not txt.endswith('..') and len(txt.split()) < 7:
            i = inner.rfind('.')
            inner = inner[:i] + inner[i+1:]
        return m.group(1) + inner + m.group(3)
    return re.sub(r'(<h[123][^>]*>)(.*?)(</h[123]>)', fix, doc, flags=re.S)

def page(path, title, desc, body, overlay=False, jsonld=None, image='/assets/img/og-volta.jpg', index=True, extra_head=''):
    canonical = SITE + path
    ld = ''.join(f'<script type="application/ld+json">{json.dumps(j, ensure_ascii=False)}</script>' for j in (jsonld or []))
    doc = f'''<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(title)}</title>
<meta name="description" content="{E(desc)}">
{'<meta name="robots" content="noindex,follow">' if not index else ''}
<link rel="canonical" href="{canonical}">
<meta property="og:type" content="website"><meta property="og:locale" content="es_ES"><meta property="og:site_name" content="Volta BCN">
<meta property="og:title" content="{E(title)}"><meta property="og:description" content="{E(desc)}">
<meta property="og:url" content="{canonical}"><meta property="og:image" content="{SITE}{image}">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#1a1a1a">
<link rel="icon" href="/assets/img/favicon.svg" type="image/svg+xml">
<link rel="preload" href="/assets/fonts/montserrat.woff" as="font" type="font/woff" crossorigin>
<link rel="stylesheet" href="/assets/css/volta.css?v=1791980866">
{extra_head}{ld}
</head>
<body>
{header(path, overlay)}
<main id="main">
{body}
</main>
{footer()}
<script src="https://cdn.jsdelivr.net/npm/@emailjs/browser@3/dist/email.min.js" defer></script>
<script src="/assets/js/volta.js?v=1791980866" defer></script>
</body>
</html>
'''
    doc = re.sub(r'<div class="eyebrow">.*?</div>\s*', '', doc)   # sin mini títulos sobre los apartados
    doc = sin_punto(doc)
    doc = silabas.html(doc)                                           # guiones suaves para el texto justificado
    out = ROOT / path.lstrip('/') / 'index.html' if path.endswith('/') else ROOT / path.lstrip('/')
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(doc, encoding='utf-8')
    if index:
        PAGES.append(path)

def crumbs(*items):
    parts = ['<a href="/">Inicio</a>'] + [f'<a href="{h}">{E(t)}</a>' if h else f'<span aria-current="page" style="margin:0">{E(t)}</span>' for t, h in items]
    return '<nav class="crumbs" aria-label="Migas de pan">' + '<span>/</span>'.join(parts) + '</nav>'

def breadcrumb_ld(*items):
    lst = [('Inicio', '/')] + list(items)
    return {"@context": "https://schema.org", "@type": "BreadcrumbList",
            "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": n, "item": SITE + h} for i, (n, h) in enumerate(lst)]}

ORG = {"@context": "https://schema.org", "@type": "RealEstateAgent", "name": "Volta BCN", "url": SITE + "/",
       "email": EMAIL, "telephone": TEL.replace(' ', ''), "areaServed": {"@type": "City", "name": "Barcelona"},
       "description": "Gestión integral de propiedades, alquiler temporal y corporativo y compraventa de viviendas en Barcelona."}

# ───────────────────────── componentes ─────────────────────────
def badge(p):
    if p['estado'] == 'vendido': return '<span class="badge sold">Vendido</span>'
    if p['estado'] == 'alquilado': return '<span class="badge sold">Alquilado</span>'
    if p['operacion'] == 'alquiler': return f'<span class="badge rent">{E(p["modalidad"])}</span>'
    return '<span class="badge">En venta</span>'

def meta(p):
    bits = [f"{p['superficie']} m²", f"{p['habitaciones']} hab."]
    b = str(p.get('banos') or '')
    if b.isdigit(): bits.append(f"{b} {'baño' if b == '1' else 'baños'}")
    elif b: bits.append(re.sub(r'^1\b', '1 baño', b))
    else: bits.append(next((c for c in p['caracteristicas'] if 'suite' in c), ''))
    return ''.join(f'<span>{E(b)}</span>' for b in bits if b)

def card(p, cls='', thumb=True, data=False, n=1):
    attrs = (f' data-item data-barrio="{E(p["distrito"])}" data-hab="{p["habitaciones"]}" data-estado="{p["estado"]}"' if data else '')
    return f'''<a class="prop reveal {cls}" href="{url_of(p)}"{attrs}>
  <div class="media"><img src="{foto(p, n, thumb)}" alt="{E(p['alts'][n-1])} · {E(p['titulo'])}" loading="lazy" width="900" height="675">{badge(p)}</div>
  <div class="info"><div class="zone">{E(p['barrio'])}</div><h3>{E(p['titulo'])}</h3>
    <div class="meta">{meta(p)}</div><span class="more">Ver propiedad</span></div>
</a>'''

def consent():
    return '''<label class="consent"><input type="checkbox" name="privacidad" required> <span>He leído y acepto la <a href="/privacidad/">política de privacidad</a> y autorizo a Volta a contactarme en relación con esta solicitud.</span></label>'''

def contact_form(kind, button='Enviar', interests=None, inmueble=None, message_ph='Cuéntanos qué necesitas', checked=None):
    ints = ''
    if interests:
        ints = '<fieldset class="field"><legend>Me interesa</legend><div class="choices">' + ''.join(
            f'<label><input type="checkbox" name="interes" value="{E(i)}"{" checked" if i == checked else ""}><span>{E(i)}</span></label>' for i in interests) + '</div></fieldset>'
    hid = f'<input type="hidden" name="inmueble" value="{E(inmueble)}">' if inmueble else ''
    return f'''<form class="form" data-form="{E(kind)}" novalidate>
  {hid}
  <div class="field"><label for="{kind}-n">Nombre</label><input id="{kind}-n" type="text" name="nombre" autocomplete="name" required></div>
  <div class="row"><div class="field"><label for="{kind}-t">Teléfono</label><input id="{kind}-t" type="tel" name="telefono" autocomplete="tel" required></div>
  <div class="field"><label for="{kind}-e">Email</label><input id="{kind}-e" type="email" name="email" autocomplete="email" required></div></div>
  {ints}
  <div class="field"><label for="{kind}-m">Mensaje</label><textarea id="{kind}-m" name="mensaje" placeholder="{E(message_ph)}"></textarea></div>
  {consent()}
  <button class="btn btn-primary" type="submit" data-label="{E(button)}">{E(button)}</button>
  <p class="form-msg" role="status" hidden></p>
</form>'''

BARRIOS = open(ROOT / 'data/barrios.html', encoding='utf-8').read()

def tasador(heading_tag='h2'):
    return f'''<div class="tasador">
  <div class="reveal">
    <div class="eyebrow">Valora tu inmueble</div>
    <{heading_tag} class="display">Cuánto vale <em>tu piso?</em></{heading_tag}>
    <p class="lead" style="margin-top:1.4rem">Obtén una estimación orientativa del valor de venta y de la renta mensual de tu vivienda, calculada con datos de mercado por barrio. Después lo revisamos contigo, sin compromiso.</p>
    <div class="tas-steps">
      <div><span class="emo" aria-hidden="true">🏙️</span><span class="t"><b>Datos por barrio</b>Precios actualizados zona a zona</span></div>
      <div><span class="emo" aria-hidden="true">⚖️</span><span class="t"><b>Regulación incluida</b>Impacto real de la Ley de Vivienda en Cataluña</span></div>
      <div><span class="emo" aria-hidden="true">📊</span><span class="t"><b>Venta y alquiler</b>Comparativa completa de opciones</span></div>
    </div>
  </div>
  <div class="tas-box reveal">
    <form class="form" data-tasador novalidate>
      <div class="field"><label for="tz-b">Barrio</label><select id="tz-b" name="barrio" required><option value="">Selecciona un barrio</option>{BARRIOS}</select></div>
      <div class="row"><div class="field"><label for="tz-m">Metros cuadrados</label><input id="tz-m" type="number" name="metros" min="20" max="1000" placeholder="Ej. 85" required></div>
      <div class="field"><label for="tz-h">Habitaciones</label><select id="tz-h" name="habitaciones" required><option value="">Selecciona</option><option>1</option><option>2</option><option>3</option><option>4</option><option value="5 o más">5 o más</option></select></div></div>
      <div class="field"><label for="tz-s">Estado</label><select id="tz-s" name="estado" required><option value="">Selecciona</option><option value="reformar">A reformar</option><option value="bueno">Buen estado</option><option value="reformado">Reformado</option><option value="lujo">Lujo / alta calidad</option></select></div>
      <fieldset class="field"><legend>Qué te planteas?</legend><div class="choices">
        <label><input type="radio" name="interes" value="Vender" required><span>Vender</span></label>
        <label><input type="radio" name="interes" value="Alquilar"><span>Alquilar</span></label>
        <label><input type="radio" name="interes" value="Delegar la gestión"><span>Delegar la gestión</span></label>
        <label><input type="radio" name="interes" value="Aún no lo sé"><span>Aún no lo sé</span></label></div></fieldset>
      <div class="field"><label for="tz-n">Nombre</label><input id="tz-n" type="text" name="nombre" autocomplete="name" required></div>
      <div class="row"><div class="field"><label for="tz-t">Teléfono</label><input id="tz-t" type="tel" name="telefono" autocomplete="tel" required></div>
      <div class="field"><label for="tz-e">Email</label><input id="tz-e" type="email" name="email" autocomplete="email" required></div></div>
      {consent()}
      <button class="btn btn-primary" type="submit">Calcular estimación</button>
      <p class="form-msg" role="status" hidden></p>
    </form>
    <div class="result" aria-live="polite">
      <div class="two"><div><small>Valor de venta estimado</small><b data-r="venta">—</b><span class="rg" data-r="venta-rg"></span></div>
      <div><small>Renta mensual estimada</small><b data-r="alq">—</b><span class="rg" data-r="alq-rg"></span></div></div>
      <p class="disc">Estimación orientativa calculada con precios medios por barrio. No es una tasación oficial: cada vivienda requiere una visita para valorarla con precisión.</p>
    </div>
  </div>
</div>'''

def stars(n):
    return '<span class="stars" aria-label="' + f'{n} de 5">' + '★' * n + '<i>' + '★' * (5 - n) + '</i></span>'

AVG = sum(t['valoracion'] for t in TESTI) / len(TESTI)
AVG_S = f'{AVG:.1f}'.replace('.', ',')

def testimonials_block():
    slides = ''.join(f'''<div class="quote-slide{' on' if i == 0 else ''}"><blockquote>{E(t['texto'])}</blockquote>
      <p class="who"><b>{E(t['nombre'])}</b> · {E(t['rol'])} · {E(t['barrio'])} &nbsp; {stars(t['valoracion'])}</p></div>''' for i, t in enumerate(TESTI[:8]))
    return f'''<section class="section" aria-labelledby="t-h"><div class="wrap testi">
  <div class="score reveal"><div class="eyebrow">Opiniones</div><h2 id="t-h" class="sr-only">Opiniones de propietarios</h2>
    <b>{AVG_S}</b>{stars(5)}<p>Valoración media de {len(TESTI)} propietarios que confían en Volta.</p></div>
  <div class="reveal"><div class="quote-slider" data-slider>{slides}</div>
    <div class="slider-nav"><button class="prev" type="button" aria-label="Opinión anterior">←</button><button class="next" type="button" aria-label="Opinión siguiente">→</button><span class="pos"></span><a class="link" href="/opiniones/">Ver las {len(TESTI)} opiniones</a></div></div>
</div></section>'''

CORP = [('amazon','Amazon'),('apple','Apple'),('samsung','Samsung'),('facebook','Facebook'),('netflix','Netflix'),('coca-cola','Coca-Cola'),
        ('tesla','Tesla'),('audi','Audi'),('cupra','Cupra'),('byd','BYD'),('siemens','Siemens'),('lg','LG'),('cisco','Cisco'),('oracle','Oracle'),
        ('accenture','Accenture'),('capgemini','Capgemini'),('deloitte','Deloitte'),('ey','EY'),('kpmg','KPMG'),('pwc','PwC'),
        ('inditex','Inditex'),('mango','Mango'),('desigual','Desigual'),('puig','Puig'),('grifols','Grifols'),('naturgy','Naturgy'),
        ('danone','Danone'),('condis','Condis'),('fc-barcelona','FC Barcelona'),('rcd-espanyol','RCD Espanyol'),('americas-cup',"America's Cup")]
CORP_TEXT = ['Nestlé', 'Glovo']   # sin logo en el material facilitado
TALL = {'apple','audi','cupra','fc-barcelona','rcd-espanyol','americas-cup','condis','cisco'}
def corp_block():
    logos = ''.join(f'<li{" class=\"tall\"" if k in TALL else ""}><img src="/assets/img/empresas/{k}.png" alt="{E(n)}" loading="lazy"></li>' for k, n in CORP)
    logos += ''.join(f'<li class="txt">{E(n)}</li>' for n in CORP_TEXT)
    return f'''<section class="section bg-light" aria-labelledby="c-h"><div class="wrap">
  <div class="corp reveal"><div><div class="eyebrow">Alojamiento corporativo</div><h2 id="c-h" class="display">La confianza de <em>grandes compañías.</em></h2></div>
    <p class="lead">Nos hace mucha ilusión haber trabajado de la mano de estas compañías y haber alojado a sus profesionales en Barcelona. Cada estancia ha sido una oportunidad para demostrar lo que mejor sabemos hacer: ofrecer viviendas de calidad y un servicio cercano, a la altura de empresas nacionales e internacionales tan exigentes.</p></div>
  <ul class="corp-logos reveal" aria-label="Empresas cuyos profesionales hemos alojado">{logos}</ul>
</div></section>'''

STEPS = [('Conocemos tu vivienda', 'Visitamos el inmueble, escuchamos lo que necesitas y te proponemos la estrategia y la modalidad de alquiler que mejor encajan.'),
         ('La preparamos y la comercializamos', 'Coordinamos la puesta a punto y las fotografías, publicamos el anuncio y organizamos las visitas.'),
         ('Elegimos al inquilino contigo', 'Seleccionamos perfiles solventes, formalizamos el contrato y hacemos la entrada en la vivienda.'),
         ('La cuidamos durante toda la estancia', 'Atendemos al inquilino, resolvemos incidencias con nuestro equipo de mantenimiento y te mantenemos informado.')]
def steps_block(dark=False, title='Cómo <em>trabajamos.</em>', orange=False):
    s = ''.join(f'<div class="step reveal"><h3>{t}</h3><p>{d}</p></div>' for t, d in STEPS)
    return f'''<section class="section{' bg-dark' if dark else ''}{' bg-orange' if orange else ''}" aria-labelledby="s-h"><div class="wrap">
  <div class="eyebrow">El proceso</div><h2 id="s-h" class="display">{title}</h2>
  <div class="steps">{s}</div></div></section>'''

PILLARS = [('Un único interlocutor para el inquilino', 'El inquilino se comunica directamente con Volta para resolver consultas, incidencias y cualquier necesidad de la vivienda. Tú no recibes esas llamadas.', ''),
           ('Equipo interno de mantenimiento', 'Contamos con un equipo propio que nos permite coordinar reparaciones, mantenimiento y necesidades operativas con más agilidad y control.', ' key'),
           ('Tranquilidad para el propietario', 'Delegas la gestión diaria en un equipo profesional, mantienes la visibilidad sobre tu inmueble y participas en las decisiones que requieren tu autorización.', '')]
def pillars():
    return '<div class="pillars">' + ''.join(f'<div class="pillar reveal{k}"><span class="n">0{i+1}</span><h3>{t}</h3><p>{d}</p></div>' for i, (t, d, k) in enumerate(PILLARS)) + '</div>'

def compare():
    trad = ['Comercialización', 'Visitas', 'Selección de inquilino', 'Formalización del contrato']
    vol = ['Comercialización', 'Selección de inquilinos', 'Formalización del contrato']
    plus = ['Atención al inquilino durante toda la estancia', 'Gestión de incidencias', 'Mantenimiento con equipo propio', 'Limpiezas', 'Check-in y check-out', 'Supervisión de la vivienda', 'Gestión continuada']
    return f'''<div class="compare reveal">
  <div><h3>Gestión habitual de un alquiler</h3><ul>{''.join(f'<li>{x}</li>' for x in trad)}<li class="end">Habitualmente, la intervención termina con la firma</li></ul></div>
  <div class="vol"><h3>Gestión integral <span>Volta</span></h3><ul>{''.join(f'<li>{x}</li>' for x in vol)}{''.join(f'<li class="plus">{x}</li>' for x in plus)}</ul></div>
</div>
<p class="compare-note">Muchas agencias hacen un trabajo excelente encontrando inquilino. Nuestra propuesta es distinta: seguimos a cargo de la vivienda después de la firma.</p>'''

def cta_band():
    return f'''<section class="section bg-dark" aria-labelledby="cta-h"><div class="wrap cta-band">
  <div class="reveal"><div class="eyebrow">Hablemos</div><h2 id="cta-h" class="display">Cuéntanos qué tienes en mente. <em>Te escuchamos.</em></h2>
    <p class="lead" style="margin-top:1.4rem">Tanto si quieres delegar la gestión de tu vivienda como si buscas piso o estás pensando en vender, una conversación es el mejor punto de partida.</p>
    <div class="actions" style="margin-top:2rem"><a class="btn btn-primary" href="/contacto/">Escríbenos</a></div></div>
  <div class="channels reveal">
    <a href="{TEL_LINK}"><span>{TEL}</span><small>Teléfono</small></a>
    <a href="{WA_LINK}" target="_blank" rel="noopener"><span>Escríbenos por WhatsApp</span><small>WhatsApp</small></a>
    <a href="mailto:{EMAIL}"><span>{EMAIL}</span><small>Email</small></a>
  </div></div></section>'''

# ───────────────────────── páginas ─────────────────────────
def home():
    avail = [p for p in PROPS if p['estado'] == 'disponible']
    big = next((p for p in avail if p['operacion'] == 'venta'), avail[0])
    rest = [p for p in avail if p['id'] in ('piso-obra-nueva-poblenou-22', 'atico-terraza-eixample')]
    hero_alt = 'Salón con vigas de madera de un apartamento gestionado por Volta en el Gòtic'
    body = f'''
<section class="hero" aria-labelledby="h1">
  <div class="hero-badges wrap"><img src="/assets/img/api-certificado-blanco.png" alt="Miembros de API y AICAT, agentes inmobiliarios certificados" width="1200" height="255"></div>
  <div class="hero-bg" role="img" aria-label="{hero_alt}" style="background-image:url(/assets/img/hero.jpg)"></div>
  <div class="hero-main"><div class="wrap"><div style="max-width:780px">
    <div class="eyebrow">Gestión · Alquiler · Compraventa</div>
    <h1 id="h1">Tu propiedad, <span>nuestra gestión.</span></h1>
    <p class="lead hero-lead">Gestionamos, alquilamos y comercializamos propiedades en Barcelona, ofreciendo un servicio integral y personalizado para que cada propietario disfrute de su inversión sin ocuparse de la gestión diaria.</p>
    <div class="actions"><a class="btn btn-primary" href="/propietarios/gestion-integral/">Descubre nuestra gestión</a><a class="btn btn-ghost" href="#inmuebles">Explora nuestros inmuebles</a></div>
  </div></div></div>
  <nav class="doors" aria-label="Accesos rápidos">
    <a class="door" href="/propietarios/gestion-integral/"><span><small>Soy propietario</small><b>Que Volta gestione mi piso</b></span><span class="arr" aria-hidden="true">→</span></a>
    <a class="door" href="/alquilar/"><span><small>Busco vivienda</small><b>Alquiler temporal y corporativo</b></span><span class="arr" aria-hidden="true">→</span></a>
    <a class="door" href="/comprar/"><span><small>Comprar o vender</small><b>Compraventa en Barcelona</b></span><span class="arr" aria-hidden="true">→</span></a>
  </nav>
</section>

<section class="section" aria-labelledby="i-h"><div class="wrap intro">
  <div class="reveal"><div class="eyebrow">Quiénes somos</div><h2 id="i-h" class="sr-only">Quiénes somos</h2>
    <p class="big">Somos un equipo de Barcelona que <em>cuida</em> viviendas: las alquilamos, las vendemos y, sobre todo, las gestionamos.</p>
    <figure class="intro-photo"><img src="/assets/img/visita.jpg" alt="Agente de Volta enseñando un piso a una pareja interesada en alquilarlo" loading="lazy" width="1400" height="933"></figure></div>
  <div class="reveal"><p class="lead">Una inmobiliaria suele terminar su trabajo cuando se firma el contrato. Nosotros empezamos ahí. Comercializamos tu vivienda y, después, seguimos a cargo de ella durante toda la estancia del inquilino: atendemos sus llamadas, coordinamos el mantenimiento y te mantenemos informado.</p>
    <div class="cols"><div><b>Para propietarios</b>Gestión integral de alquileres, venta y valoración de tu vivienda.</div><div><b>Para quien busca casa</b>Viviendas en alquiler temporal, corporativo y en venta en Barcelona.</div></div>
    <p style="margin-top:1.6rem"><a class="link" href="/nosotros/">Conoce Volta</a></p>
    <div class="api-badge"><img src="/assets/img/api-certificado.png" alt="API – Col·legis i associació d'agents immobiliaris (certificado) y AICAT – Agents immobiliaris de Catalunya" loading="lazy" width="1200" height="255"></div></div>
</div></section>

<section class="section bg-orange" id="valoracion" aria-label="Valoración de inmuebles"><div class="wrap">{tasador()}</div></section>

<section class="section" aria-labelledby="sv-h"><div class="wrap">
  <div class="eyebrow">Servicios</div><h2 id="sv-h" class="display">Tres formas de trabajar <em>con nosotros.</em></h2>
  <div class="services">
    <article class="svc-main reveal"><div class="ph" style="background-image:url(/inmuebles/eixample/01.jpg)" role="img" aria-label="Salón de un ático gestionado por Volta en el Eixample"></div>
      <div class="bd"><span class="tag">Nuestro servicio principal</span><h3 class="h3">Gestión integral de propiedades</h3>
      <p style="margin-top:.9rem">Nos encargamos de la comercialización y de toda la gestión operativa del inmueble durante la estancia del inquilino: atención, incidencias, mantenimiento, limpiezas, check-in y check-out.</p>
      <a class="link" href="/propietarios/gestion-integral/">Cómo funciona la gestión</a></div></article>
    <div class="svc-side">
      <article class="svc reveal"><span class="num">02</span><h3 class="h3">Alquiler de inmuebles</h3><p>Comercializamos viviendas de alquiler temporal y corporativo en Barcelona, preparadas para entrar a vivir.</p><a class="link" href="/alquilar/">Ver viviendas en alquiler</a></article>
      <article class="svc reveal"><span class="num">03</span><h3 class="h3">Compraventa</h3><p>Ayudamos a propietarios a vender su vivienda y a compradores a encontrar la propiedad que buscan.</p><a class="link" href="/propietarios/vender/">Vender con Volta</a></article>
    </div>
  </div>
</div></section>

<section class="section diff-light bg-light" aria-labelledby="d-h"><div class="wrap">
  <div class="eyebrow">Nuestra diferencia</div>
  <div class="diff-top">
    <div>
    <h2 id="d-h" class="diff-quote reveal">Tu inquilino nos llama a nosotros. <em>Tú disfrutas de tu propiedad.</em></h2>
    <p class="lead" style="margin-top:1.8rem">Cuando se estropea el lavavajillas, falla la caldera o surge una duda con los suministros, el inquilino contacta con Volta. Nuestro equipo recibe la consulta, coordina la solución y supervisa que la vivienda funcione. Tú solo intervienes cuando hace falta tu autorización.</p>
    </div>
    <figure class="diff-photo reveal"><img src="/assets/img/mantenimiento.jpg" alt="Técnico de mantenimiento trabajando colgado en la fachada de un edificio" loading="lazy" width="1400" height="1173"></figure>
  </div>
  {pillars()}
  <p style="margin-top:3rem"><a class="link" href="/propietarios/gestion-integral/">Todo lo que incluye la gestión integral</a></p>
</div></section>

<section class="section" id="inmuebles" aria-labelledby="p-h"><div class="wrap">
  <div style="display:flex;flex-wrap:wrap;justify-content:space-between;align-items:flex-end;gap:1.4rem">
    <div><div class="eyebrow">Inmuebles</div><h2 id="p-h" class="display">Viviendas que <em>gestionamos.</em></h2></div>
    <div class="actions"><a class="link" href="/alquilar/">Ver alquileres</a><a class="link" href="/comprar/">Ver viviendas en venta</a></div>
  </div>
  <div class="feat">{card(big, 'big', thumb=False)}<div class="stack">{''.join(card(p, n=7 if p['id'] == 'atico-terraza-eixample' else 1) for p in rest)}</div></div>
</div></section>

{corp_block()}
{steps_block(orange=True)}
{testimonials_block()}
{cta_band()}'''
    page('/', 'Volta BCN | Gestión integral, alquiler y venta de viviendas en Barcelona',
         'Gestionamos, alquilamos y comercializamos viviendas en Barcelona. Atención al inquilino y equipo propio de mantenimiento durante toda la estancia.',
         body, overlay=True, jsonld=[ORG])

def catalog(op):
    is_rent = op == 'alquiler'
    path = '/alquilar/' if is_rent else '/comprar/'
    items = [p for p in PROPS if p['operacion'] == op]
    items.sort(key=lambda p: p['estado'] != 'disponible')
    distritos = sorted({p['distrito'] for p in items})
    opts = ''.join(f'<option>{E(d)}</option>' for d in distritos)
    estado = '' if is_rent else '<label>Disponibilidad<select data-filter="estado"><option value="">Todas</option><option value="disponible">En venta</option><option value="vendido">Vendidas</option></select></label>'
    title = 'Viviendas en <em>alquiler.</em>' if is_rent else 'Viviendas en <em>venta.</em>'
    lead = ('Pisos amueblados y preparados para entrar a vivir, en alquiler temporal y corporativo. Durante toda la estancia, el inquilino cuenta con Volta como interlocutor para cualquier necesidad.'
            if is_rent else 'Viviendas en venta en Barcelona y algunas de las operaciones que hemos acompañado. Pide información de cualquiera de ellas y te atendemos personalmente.')
    body = f'''<section class="page-head cat-head"><div class="wrap">{crumbs(('Alquilar' if is_rent else 'Comprar', None))}
  <div class="eyebrow">{'Alquilar' if is_rent else 'Comprar'}</div><h1 class="display">{title}</h1><p class="lead">{lead}</p>
  <img class="cat-sellos" src="/assets/img/sellos.png" alt="Miembros de API y AICAT, agentes inmobiliarios certificados" width="1400" height="303"></div></section>
<section class="section tight cat-list"><div class="wrap" data-catalog>
  <div class="catalog-tools" role="search">
    <label>Zona<select data-filter="barrio"><option value="">Toda Barcelona</option>{opts}</select></label>
    <label>Habitaciones<select data-filter="hab"><option value="">Cualquiera</option><option value="1">1 o más</option><option value="2">2 o más</option><option value="3">3 o más</option></select></label>
    {estado}<span class="count" data-count aria-live="polite"></span></div>
  <div class="grid">{''.join(card(p, data=True) for p in items)}</div>
  <p class="empty" data-empty hidden>No hay inmuebles con esos criterios ahora mismo. <a class="link" href="/contacto/">Cuéntanos qué buscas</a></p>
</div></section>
<section class="section bg-light"><div class="wrap split">
  <div><div class="eyebrow">{'Buscas algo concreto?' if is_rent else 'Tienes una vivienda en venta?'}</div><h2 class="display">{'Te ayudamos a <em>encontrarlo.</em>' if is_rent else 'Hablemos de <em>tu venta.</em>'}</h2>
    <p class="lead" style="margin-top:1.4rem">{'No todas nuestras viviendas se publican. Dinos qué necesitas, para cuándo y para cuánto tiempo, y te proponemos opciones.' if is_rent else 'Valoramos tu vivienda, preparamos la comercialización y te acompañamos hasta la firma.'}</p></div>
  <div>{contact_form('busqueda-alquiler' if is_rent else 'busqueda-compra', 'Enviar solicitud', message_ph='Zona, fechas, número de personas, presupuesto orientativo…' if is_rent else 'Zona, tipo de vivienda, si buscas comprar o vender…')}</div>
</div></section>'''
    page(path, ('Pisos en alquiler temporal y corporativo en Barcelona' if is_rent else 'Pisos en venta en Barcelona') + ' | Volta BCN',
         ('Viviendas amuebladas en alquiler temporal y corporativo en Barcelona, con atención al inquilino durante toda la estancia.' if is_rent
          else 'Viviendas en venta en Barcelona comercializadas por Volta. Solicita información y visita.'),
         body, jsonld=[ORG, breadcrumb_ld(('Alquilar' if is_rent else 'Comprar', path))])

def ficha(p):
    path = url_of(p)
    is_rent = p['operacion'] == 'alquiler'
    fotos = [foto(p, n) for n in range(1, p['fotos'] + 1)]
    def pick(*keys):
        for k in keys:
            for j, a in enumerate(p['alts']):
                if a.lower().startswith(k):
                    return j
        return None
    idx = []
    for keys in (('salón', 'sala', 'comedor'), ('cocina',), ('dormitorio', 'suite', 'tercer dormitorio', 'segundo dormitorio'), ('baño', 'aseo')):
        j = pick(*keys)
        if j is not None and j not in idx: idx.append(j)
    if p.get('galeria'): idx = list(p['galeria'])
    if len(idx) < 5:
        extra = pick('terraza', 'piscina', 'balcón', 'vistas', 'despacho', 'comedor', 'segundo dormitorio', 'recibidor')
        if extra is not None and extra not in idx: idx.append(extra)
    for j in range(p['fotos']):
        if len(idx) >= 5: break
        if j not in idx: idx.append(j)
    gal = ''.join(f'<button type="button" data-open="{i}" aria-label="Ampliar foto: {E(p["alts"][i])}"><img src="{foto(p, i+1, n > 0)}" alt="{E(p["alts"][i])}" {"" if n == 0 else 'loading="lazy"'}></button>' for n, i in enumerate(idx))
    lat, lon = p['mapa']; d = 0.012
    bbox = f'{lon-d*1.6:.4f}%2C{lat-d:.4f}%2C{lon+d*1.6:.4f}%2C{lat+d:.4f}'
    services = (['Atención directa al inquilino durante toda la estancia', 'Gestión de incidencias', 'Mantenimiento con equipo propio', 'Limpiezas coordinadas', 'Check-in y check-out', 'Supervisión de la vivienda']
                if is_rent else ['Información completa del inmueble', 'Visitas acompañadas', 'Asesoramiento durante la negociación', 'Acompañamiento hasta la firma'])
    planos = ''
    if p.get('planos'):
        planos = '<div class="block"><h2>Planos</h2>' + ''.join(f'<a href="{x}" target="_blank" rel="noopener"><img src="{x}" alt="Plano de {E(p["titulo"])}" loading="lazy" style="border:1px solid var(--line)"></a>' for x in p['planos']) + '</div>'
    sold = p['estado'] in ('vendido', 'alquilado')
    op_label = 'Vendido' if p['estado'] == 'vendido' else ('Alquilado' if p['estado'] == 'alquilado' else (p['modalidad'] if is_rent else 'Venta'))
    banos_fact = f"<div><small>Baños</small><b>{E(p['banos'])}</b></div>" if p.get('banos') else '<div><small>Distribución</small><b>3 suites</b></div>'
    aside_title = 'Buscas algo parecido?' if sold else ('Solicita información' if not is_rent else 'Solicita información o visita')
    aside = f'''<aside class="aside" aria-labelledby="form-h"><h2 id="form-h">{aside_title}</h2>
  <p class="small muted">{'Esta vivienda ya no está disponible, pero podemos ayudarte a encontrar una similar.' if sold else 'Te respondemos personalmente con toda la información y la disponibilidad.'}</p>
  <div class="price-note"><span>Precio</span><b>Solicitar información</b></div>
  {contact_form('ficha', 'Solicitar información' if not sold else 'Enviar', interests=None if sold else ['Más información', 'Solicitar visita'], inmueble=p['titulo'] + ' · ' + p['barrio'], message_ph='Fechas, número de personas, preguntas…' if is_rent else 'Cuéntanos qué te gustaría saber', checked=None if sold else 'Más información')}
  <p class="small muted" style="margin-top:1rem">También por <a class="link" href="{WA_LINK}" target="_blank" rel="noopener">WhatsApp</a> o en el <a href="{TEL_LINK}" style="text-decoration:underline">{TEL}</a>.</p>
</aside>'''
    body = f'''<section class="section tight" style="padding-bottom:0"><div class="wrap">
  {crumbs(('Alquilar' if is_rent else 'Comprar', '/alquilar/' if is_rent else '/comprar/'), (p['titulo'], None))}
  <div class="eyebrow">{E(op_label)} · {E(p['barrio'])}</div>
  <h1 class="display" style="max-width:20ch">{E(p['titulo'])}</h1>
  <div class="gallery">{gal}<button class="all" type="button" data-open="0">Ver las {p['fotos']} fotos</button></div>
  <div class="detail">
    <div>
      <div class="facts"><div><small>Superficie</small><b>{p['superficie']} m²</b></div><div><small>Habitaciones</small><b>{p['habitaciones']}</b></div>{banos_fact}<div><small>Operación</small><b>{E(op_label)}</b></div></div>
      <div class="prose">{''.join(f'<p>{E(x)}</p>' for x in p['descripcion'])}</div>
      <div class="block"><h2>Características</h2><ul class="ticks">{''.join(f'<li>{E(x)}</li>' for x in p['caracteristicas'])}</ul></div>
      {('<div class="block"><h2>Equipamiento</h2><ul class="ticks">' + ''.join(f'<li>{E(x)}</li>' for x in p['equipamiento']) + '</ul></div>') if p.get('equipamiento') else ''}
      <div class="block"><h2>{'Servicios Volta durante la estancia' if is_rent else 'Cómo te acompañamos'}</h2><ul class="ticks">{''.join(f'<li>{E(x)}</li>' for x in services)}</ul></div>
      {planos}
      <div class="block"><h2>Ubicación</h2>
        <iframe class="map" title="Mapa aproximado de {E(p['barrio'])}" loading="lazy" referrerpolicy="no-referrer" src="https://www.openstreetmap.org/export/embed.html?bbox={bbox}&amp;layer=mapnik"></iframe>
        <p class="map-note">Ubicación aproximada: {E(p['barrio'])}, {E(p['distrito'])}. La dirección exacta se facilita al concertar la visita.</p></div>
    </div>
    {aside}
  </div>
</div></section>
<div class="lb" id="lb" role="dialog" aria-modal="true" aria-label="Galería de fotos" hidden>
  <button class="x" type="button" aria-label="Cerrar">×</button><button class="pv" type="button" aria-label="Foto anterior">‹</button>
  <figure><img alt=""><figcaption></figcaption></figure><button class="nx" type="button" aria-label="Foto siguiente">›</button></div>
<script type="application/json" id="gallery-data">{json.dumps({'titulo': p['titulo'], 'fotos': fotos, 'alts': p['alts']}, ensure_ascii=False)}</script>
<section class="section bg-light tight"><div class="wrap" style="display:flex;flex-wrap:wrap;justify-content:space-between;align-items:center;gap:1.4rem">
  <h2 class="h3">{'Más viviendas en alquiler' if is_rent else 'Más viviendas en venta'}</h2><a class="link" href="{'/alquilar/' if is_rent else '/comprar/'}">Ver catálogo completo</a></div></section>'''
    res = {"@context": "https://schema.org", "@type": "Apartment", "name": p['titulo'], "description": p['resumen'], "url": SITE + path,
           "image": [SITE + f for f in fotos[:6]], "floorSize": {"@type": "QuantitativeValue", "value": p['superficie'], "unitCode": "MTK"},
           "numberOfRooms": p['habitaciones'],
           "address": {"@type": "PostalAddress", "addressLocality": "Barcelona", "addressRegion": "Cataluña", "addressCountry": "ES"},
           "containedInPlace": {"@type": "Place", "name": f"{p['barrio']}, {p['distrito']}, Barcelona"}}
    page(path, f"{p['titulo']} · {p['barrio']} | Volta BCN", f"{p['resumen']} {p['superficie']} m², {p['habitaciones']} hab. Solicita información.",
         body, jsonld=[res, breadcrumb_ld(('Alquilar' if is_rent else 'Comprar', '/alquilar/' if is_rent else '/comprar/'), (p['titulo'], path))],
         image=foto(p, 1))

SERVICES = ['Comercialización de inmuebles', 'Búsqueda y selección de inquilinos', 'Gestión de visitas', 'Formalización de contratos',
            'Atención directa a los inquilinos', 'Gestión de incidencias', 'Equipo interno de mantenimiento y reparaciones', 'Coordinación de limpiezas',
            'Gestión de check-in y check-out', 'Supervisión de viviendas', 'Coordinación de suministros', 'Preparación y puesta a punto de inmuebles',
            'Seguimiento administrativo y operativo']

def gestion():
    path = '/propietarios/gestion-integral/'
    lis = ''.join(f'<li{" class=\"hl\"" if "mantenimiento" in s or "Atención" in s else ""}>{s}</li>' for s in SERVICES)
    body = f'''<section class="page-hero"><div class="txt">{crumbs(('Propietarios', None), ('Gestión integral', None))}
  <div class="eyebrow">Gestión integral de alquileres</div>
  <h1 class="display">Mucho más que alquilar tu propiedad. <em>Nos encargamos de todo.</em></h1>
  <p class="lead" style="margin-top:1.4rem">Encontramos al inquilino adecuado y gestionamos todo lo que viene después. Desde la atención diaria hasta el mantenimiento y la resolución de incidencias, nuestro equipo cuida de tu propiedad durante toda la estancia.</p>
  <div class="actions" style="margin-top:2rem"><a class="btn btn-primary" href="#solicitud">Quiero que gestionéis mi piso</a><a class="link" href="/propietarios/valorar/">Valorar mi vivienda</a></div></div>
  <div class="img" style="background-image:url(/assets/img/gestion.jpg)" role="img" aria-label="Salón luminoso con balcón en un piso del Eixample de Barcelona"></div></section>

<section class="section diff-light bg-light"><div class="wrap">
  <div class="eyebrow">Cómo cambia tu día a día</div>
  <h2 class="diff-quote reveal">Tu inquilino nos llama a nosotros. <em>Tú disfrutas de tu propiedad.</em></h2>
  <div class="split" style="margin-top:2.4rem">
    <p class="lead">En un alquiler convencional, cuando surge una avería en el lavavajillas, un problema con la caldera o una consulta sobre suministros, el inquilino llama al propietario. Y el propietario tiene que atender la llamada, buscar un técnico y coordinar la reparación.</p>
    <p class="lead">Con Volta, el inquilino tiene a nuestro equipo como punto de contacto. Recibimos la consulta, gestionamos la incidencia, coordinamos la solución y comprobamos que todo funciona. Tú sigues informado y decides en lo que requiere tu autorización.</p>
  </div>
  {pillars()}
</div></section>

<section class="section"><div class="wrap">
  <div class="eyebrow">La diferencia</div><h2 class="display">Lo que pasa <em>después de la firma.</em></h2>
  {compare()}
</div></section>

<section class="section bg-orange"><div class="wrap split">
  <div><div class="eyebrow">Qué incluye</div><h2 class="display">Un servicio <em>completo.</em></h2>
    <p class="lead" style="margin-top:1.4rem">Adaptamos la gestión a cada vivienda y a cada propietario: alquiler temporal y corporativo, larga estancia, coliving o edificios completos.</p></div>
  <ul class="svc-list">{lis}</ul>
</div></section>

{steps_block(dark=False, title='Así trabajamos <em>contigo.</em>')}

<section class="section bg-light"><div class="wrap split">
  <div><div class="eyebrow">Una relación a largo plazo</div><h2 class="display">Tu socio inmobiliario <em>de confianza.</em></h2>
    <p class="lead" style="margin-top:1.4rem">Aunque el inquilino hable con nosotros, la relación con el propietario es la que más cuidamos. Queremos ser el equipo al que llamas para todo lo relacionado con tu vivienda, hoy y dentro de muchos años.</p></div>
  <div id="solicitud">{contact_form('gestion-integral', 'Solicitar propuesta de gestión', interests=['Alquiler temporal', 'Alquiler corporativo', 'Larga estancia', 'Aún no lo sé'], message_ph='Barrio, metros, situación actual de la vivienda…')}</div>
</div></section>
{testimonials_block()}'''
    page(path, 'Gestión integral de alquileres en Barcelona | Volta BCN',
         'Property management en Barcelona: el inquilino contacta con Volta y nuestro equipo propio de mantenimiento resuelve las incidencias. Tú delegas la gestión diaria.',
         body, jsonld=[ORG, breadcrumb_ld(('Gestión integral de alquileres', path))])

def vender():
    path = '/propietarios/vender/'
    sold = [p for p in PROPS if p['operacion'] == 'venta']
    steps = [('Valoración', 'Analizamos tu vivienda y el mercado de la zona para definir un precio de salida realista.'),
             ('Preparación', 'Te aconsejamos sobre la puesta a punto y coordinamos fotografías de calidad.'),
             ('Comercialización y visitas', 'Publicamos el inmueble, filtramos a los interesados y acompañamos cada visita.'),
             ('Hasta la firma', 'Te acompañamos en la negociación, la reserva, las arras y la firma.')]
    body = f'''<section class="page-hero"><div class="txt">{crumbs(('Propietarios', None), ('Vende tu propiedad', None))}
  <div class="eyebrow">Vende tu propiedad</div>
  <h1 class="display">Vender con criterio, <em>de principio a fin.</em></h1>
  <p class="lead" style="margin-top:1.4rem">Te ayudamos a vender tu vivienda en Barcelona con una estrategia clara, una buena presentación del inmueble y un acompañamiento cercano hasta la firma.</p>
  <div class="actions" style="margin-top:2rem"><a class="btn btn-primary" href="#solicitud">Quiero vender</a><a class="link" href="/propietarios/valorar/">Valorar mi vivienda</a></div></div>
  <div class="img" style="background-image:url(/assets/img/vender.jpg)" role="img" aria-label="Salón con balcón abierto y suelo hidráulico en Barcelona"></div></section>
<section class="section"><div class="wrap"><div class="eyebrow">El proceso</div><h2 class="display">Cómo vendemos <em>tu vivienda.</em></h2>
  <div class="steps">{''.join(f'<div class="step reveal"><h3>{t}</h3><p>{d}</p></div>' for t, d in steps)}</div></div></section>
<section class="section bg-light"><div class="wrap"><div class="eyebrow">Operaciones</div><h2 class="display">Viviendas que hemos <em>comercializado.</em></h2>
  <div class="grid" style="margin-top:3rem">{''.join(card(p) for p in sold)}</div></div></section>
<section class="section" id="solicitud"><div class="wrap split">
  <div><div class="eyebrow">Hablemos</div><h2 class="display">Cuéntanos sobre <em>tu vivienda.</em></h2><p class="lead" style="margin-top:1.4rem">Te llamamos, vemos la vivienda contigo y te damos una valoración realista antes de empezar.</p></div>
  <div>{contact_form('vender', 'Solicitar valoración para vender', message_ph='Barrio, metros, estado de la vivienda, plazos…')}</div></div></section>'''
    page(path, 'Vender tu piso en Barcelona | Volta BCN', 'Vende tu vivienda en Barcelona con Volta: valoración, preparación, comercialización, visitas y acompañamiento hasta la firma.',
         body, jsonld=[ORG, breadcrumb_ld(('Vende tu propiedad', path))])

def valorar():
    path = '/propietarios/valorar/'
    body = f'''<section class="page-banner" role="img" aria-label="Vista de Barcelona desde el Park Güell" style="background-image:url(/assets/img/valorar.jpg)"><div class="wrap">{crumbs(('Propietarios', None), ('Valora tu inmueble', None))}</div></section>
<section class="section bg-orange"><div class="wrap">{tasador('h1')}</div></section>
<section class="section bg-light"><div class="wrap split">
  <div><div class="eyebrow">Vender o alquilar</div><h2 class="display">Una decisión <em>con datos.</em></h2></div>
  <div class="prose"><p>El valor de una vivienda en Barcelona cambia mucho de un barrio a otro, y la decisión entre vender o alquilar depende de más factores que el precio: el rendimiento neto del alquiler una vez descontados gastos e impuestos, el horizonte temporal del propietario y la situación concreta del inmueble.</p>
  <p>Por eso la estimación es solo el punto de partida. Después revisamos tu caso contigo y te explicamos, sin compromiso, qué opción tiene más sentido: vender, alquilar o delegar la gestión en Volta.</p></div></div></section>'''
    page(path, 'Cuánto vale tu piso en Barcelona? Valoración orientativa | Volta BCN',
         'Calcula una estimación orientativa del valor de venta y de la renta de tu piso en Barcelona por barrio, y habla con Volta sobre vender, alquilar o delegar la gestión.',
         body, jsonld=[ORG, breadcrumb_ld(('Valora tu inmueble', path))])

def nosotros():
    path = '/nosotros/'
    body = f'''<section class="page-hero"><div class="txt">{crumbs(('Nosotros', None))}
  <div class="eyebrow">Nosotros</div><h1 class="display">Cuidamos viviendas <em>en Barcelona.</em></h1>
  <p class="lead" style="margin-top:1.4rem">Volta es una empresa especializada en gestión integral de propiedades, alquiler temporal, alquiler corporativo y comercialización inmobiliaria en Barcelona.</p></div>
  <div class="img" style="background-image:url(/assets/img/nosotros.jpg)" role="img" aria-label="Recinto modernista de Sant Pau y vistas de Barcelona hasta el Tibidabo"></div></section>
<section class="section"><div class="wrap split">
  <div><div class="eyebrow">Nuestro modelo</div><h2 class="display">Dos actividades, <em>un mismo equipo.</em></h2></div>
  <div class="prose">
    <h2 style="margin-top:0">Comercialización inmobiliaria</h2><p>Ayudamos a propietarios a comercializar sus inmuebles y a clientes a encontrar viviendas en alquiler o en compra.</p>
    <h2>Property management</h2><p>Nos encargamos de la gestión continua de las viviendas durante toda la estancia del inquilino, con un servicio personalizado tanto para el propietario como para el arrendatario. Es lo que nos diferencia: en lugar de terminar nuestro trabajo con la firma del contrato, seguimos a cargo de la vivienda.</p>
    <p>Para hacerlo bien contamos con un equipo interno de mantenimiento, que nos permite atender las necesidades de cada vivienda de forma más coordinada, ágil y personal.</p></div></div></section>
<section class="section bg-dark"><div class="wrap split">
  <div><div class="eyebrow">Nuestra filosofía</div><h2 class="display">Que el propietario <em>no tenga que preocuparse.</em></h2></div>
  <div class="prose" style="color:rgba(255,255,255,.78)"><p style="color:inherit">Creemos que tener una vivienda en alquiler no debería ser un segundo trabajo. Nuestro objetivo es que el propietario no tenga que encargarse de la gestión operativa diaria, pero que siga informado y decida en lo importante.</p>
  <p style="color:inherit">Preferimos explicar las cosas con claridad, hablar de números reales y no prometer lo que no podemos cumplir.</p></div></div></section>
<section class="section"><div class="wrap split">
  <div><div class="eyebrow">Nuestro compromiso</div><h2 class="display">Una relación <em>a largo plazo.</em></h2></div>
  <div class="prose"><p>Queremos ser el socio inmobiliario de confianza de cada propietario. Nuestra propuesta no consiste solo en encontrar un inquilino, sino en cuidar, gestionar y supervisar su propiedad de manera continuada.</p>
  <p><a class="link" href="/propietarios/gestion-integral/">Cómo funciona la gestión integral</a></p></div></div></section>
{corp_block()}
{testimonials_block()}
{cta_band()}'''
    page(path, 'Sobre Volta | Gestión integral y comercialización inmobiliaria en Barcelona',
         'Volta combina comercialización inmobiliaria y property management en Barcelona, con equipo propio de mantenimiento y atención al inquilino durante toda la estancia.',
         body, jsonld=[ORG, breadcrumb_ld(('Nosotros', path))])

def contacto():
    path = '/contacto/'
    body = f'''<section class="page-hero"><div class="txt">{crumbs(('Contacto', None))}
  <div class="eyebrow">Contacto</div><h1 class="display">Hablemos de <em>tu vivienda.</em></h1>
  <p class="lead" style="margin-top:1.4rem">Escríbenos, llámanos o mándanos un WhatsApp. Te responde una persona del equipo.</p></div>
  <div class="img" style="background-image:url(/assets/img/contacto.jpg)" role="img" aria-label="Asesora de Volta atendiendo a un propietario"></div></section>
<section class="section"><div class="wrap contact-grid">
  <div class="contact-list">
    <a href="{TEL_LINK}"><small>Teléfono</small><b>{TEL}</b></a>
    <a href="{WA_LINK}" target="_blank" rel="noopener"><small>WhatsApp</small><b>Escríbenos por WhatsApp</b></a>
    <a href="mailto:{EMAIL}"><small>Email</small><b>{EMAIL}</b></a>
    <div><small>Zona de trabajo</small><b>Barcelona</b></div>
  </div>
  <div>{contact_form('contacto', 'Enviar mensaje', interests=['Delegar la gestión', 'Vender', 'Alquilar una vivienda', 'Comprar', 'Otro'])}</div>
</div></section>'''
    page(path, 'Contacto | Volta BCN', 'Contacta con Volta: gestión integral de alquileres, alquiler temporal y corporativo y compraventa de viviendas en Barcelona.',
         body, jsonld=[ORG, breadcrumb_ld(('Contacto', path))])

def opiniones():
    path = '/opiniones/'
    ops = ''.join(f'<article class="op"><p>“{E(t["texto"])}”</p><div class="who"><b>{E(t["nombre"])}</b> · {E(t["rol"])} · {E(t["barrio"])} &nbsp; {stars(t["valoracion"])}</div></article>' for t in TESTI)
    body = f'''<section class="page-head"><div class="wrap">{crumbs(('Opiniones', None))}
  <div class="eyebrow">Opiniones</div><h1 class="display">Lo que dicen <em>nuestros propietarios.</em></h1>
  <p class="lead">Valoración media de <b>{AVG_S}</b> sobre 5, a partir de {len(TESTI)} opiniones.</p></div></section>
<section class="section tight"><div class="wrap"><div class="op-list">{ops}</div></div></section>
{cta_band()}'''
    page(path, 'Opiniones de propietarios | Volta BCN', f'{len(TESTI)} propietarios cuentan su experiencia con la gestión de Volta en Barcelona.', body,
         jsonld=[breadcrumb_ld(('Opiniones', path))])

def legal(slug, title):
    path = f'/{slug}/'
    body = f'''<section class="page-head"><div class="wrap">{crumbs((title, None))}<h1 class="display">{title}</h1></div></section>
<section class="section tight"><div class="wrap prose">
  <!-- TEXTO LEGAL PENDIENTE: sustituir este bloque por el documento facilitado por el asesor legal de Volta. -->
  <div class="notice"><p>Estamos actualizando este documento.</p><p style="margin:0">Para cualquier consulta sobre el tratamiento de tus datos o sobre esta web, escríbenos a <a href="mailto:{EMAIL}" style="text-decoration:underline">{EMAIL}</a>.</p></div>
</div></section>'''
    page(path, f'{title} | Volta BCN', f'{title} de Volta BCN.', body, index=False)

def not_found():
    body = '''<section class="section"><div class="wrap"><div class="eyebrow">Error 404</div><h1 class="display">Esta página <em>no existe.</em></h1>
<p class="lead" style="margin-top:1.4rem">Puede que el inmueble ya no esté publicado o que la dirección haya cambiado.</p>
<div class="actions" style="margin-top:2rem"><a class="btn btn-primary" href="/">Volver al inicio</a><a class="link" href="/alquilar/">Ver alquileres</a><a class="link" href="/comprar/">Ver ventas</a></div></div></section>'''
    page('/404.html', 'Página no encontrada | Volta BCN', 'La página que buscas no existe.', body, index=False)

def sitemap():
    today = datetime.date.today().isoformat()
    urls = ''.join(f'<url><loc>{SITE}{p}</loc><lastmod>{today}</lastmod></url>' for p in PAGES)
    (ROOT / 'sitemap.xml').write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n', encoding='utf-8')
    (ROOT / 'robots.txt').write_text(f'User-agent: *\nAllow: /\nDisallow: /data/\n\nSitemap: {SITE}/sitemap.xml\n', encoding='utf-8')

if __name__ == '__main__':
    home(); catalog('alquiler'); catalog('venta')
    for p in PROPS: ficha(p)
    gestion(); vender(); valorar(); nosotros(); contacto(); opiniones()
    legal('aviso-legal', 'Aviso legal'); legal('privacidad', 'Política de privacidad'); legal('cookies', 'Política de cookies')
    not_found(); sitemap()
    print(f'{len(PAGES)} páginas indexables generadas.')
