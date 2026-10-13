"""Separación silábica sencilla en español para insertar guiones suaves (&shy;)
en los párrafos justificados, de modo que no queden huecos grandes entre palabras.
Solo corta entre consonantes y vocales según las reglas básicas; nunca separa
grupos vocálicos, así que puede perder algún punto de corte pero no inventa cortes incorrectos."""
import re

V = set('aeiouáéíóúüAEIOUÁÉÍÓÚÜ')
INSEP = {'pr', 'pl', 'br', 'bl', 'fr', 'fl', 'tr', 'dr', 'cr', 'cl', 'gr', 'gl', 'kr', 'kl', 'ch', 'll', 'rr'}
SHY = '­'

def puntos(w):
    """Índices donde se puede cortar la palabra w."""
    low = w.lower()
    vpos = [i for i, c in enumerate(low) if c in V]
    cortes = []
    for a, b in zip(vpos, vpos[1:]):
        if b == a + 1:
            continue  # grupo vocálico: no se separa
        cons = low[a + 1:b]
        n = len(cons)
        if n == 1:
            cortes.append(a + 1)
        elif n == 2:
            cortes.append(a + 1 if cons in INSEP else a + 2)
        elif n == 3:
            cortes.append(a + 2 if cons[1:] in INSEP else a + 3)
        elif n == 4:
            cortes.append(a + 3)
    return [c for c in cortes if 2 <= c <= len(w) - 3]

def palabra(w):
    if len(w) < 7:
        return w
    out, prev = [], 0
    for c in puntos(w):
        out.append(w[prev:c]); prev = c
    out.append(w[prev:])
    return SHY.join(out)

WORD = re.compile(r'[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+')

def texto(s):
    return WORD.sub(lambda m: palabra(m.group(0)), s)

TAG = re.compile(r'(<[^>]+>)')
def html(doc):
    """Inserta guiones suaves solo en el texto que está dentro de <p> o de <li> de párrafos."""
    parts = TAG.split(doc)
    depth, skip = 0, 0
    for i, part in enumerate(parts):
        if part.startswith('<'):
            t = part[1:].split()[0].rstrip('>').lower() if len(part) > 2 else ''
            if t in ('script', 'style', 'title', 'h1', 'h2', 'h3', 'button', 'label', 'select', 'a'):
                skip += 1
            elif t in ('/script', '/style', '/title', '/h1', '/h2', '/h3', '/button', '/label', '/select', '/a'):
                skip = max(0, skip - 1)
            elif t == 'p' and 'class="big"' not in part and 'hero-lead' not in part:
                depth += 1
            elif t == '/p':
                depth = max(0, depth - 1)
        elif depth and not skip and part.strip():
            parts[i] = texto(part)
    return ''.join(parts)

if __name__ == '__main__':
    for w in ['comercializamos', 'personalizado', 'propietario', 'mantenimiento', 'inmobiliaria', 'Barcelona', 'estancia', 'coordinamos', 'llamadas', 'construcción']:
        print(palabra(w).replace(SHY, '-'))
