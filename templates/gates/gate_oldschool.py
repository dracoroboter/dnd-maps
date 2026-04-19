"""
Plugin OLDSCHOOL: gate renderer.
Chiamato dopo il rendering base dei passage.

render_gate(gate, orient, px, py, pw, ph, tile, sw, L)
  gate   : dict dall'enrichment {type, state, x, y}
  orient : 'h' | 'v'  (dal passage corrispondente)
  px,py  : pixel top-left del passage (già scalati)
  pw,ph  : pixel width/height del passage
  tile   : dimensione tile in pixel
  sw     : stroke-width base
  L      : lista SVG
"""
import random, math


def _j(x1, y1, x2, y2, rng, amp=0.6):
    mx = x1+(x2-x1)*0.5 + rng.uniform(-amp, amp)
    my = y1+(y2-y1)*0.5 + rng.uniform(-amp, amp)
    return f'<path d="M {x1:.1f},{y1:.1f} L {mx:.1f},{my:.1f} L {x2:.1f},{y2:.1f}" stroke="black" stroke-width="{sw_g}" fill="none"/>'


def render_gate(gate, orient, px, py, pw, ph, tile, sw, L):
    global sw_g
    sw_g = sw
    gtype = gate.get('type', 'door')
    state = gate.get('state', 'closed')
    rng   = random.Random(hash((px, py, gtype, state)))
    cx, cy = px + pw/2, py + ph/2
    d = max(2, tile//4)  # profondità stipite

    if gtype == 'door':
        _render_door(state, orient, px, py, pw, ph, cx, cy, d, tile, sw, rng, L)
    elif gtype == 'portcullis':
        _render_portcullis(state, orient, px, py, pw, ph, cx, cy, d, tile, sw, rng, L)
    elif gtype == 'arch':
        _render_arch(orient, px, py, pw, ph, cx, cy, d, tile, sw, rng, L)
    elif gtype == 'secret':
        _render_secret(state, orient, px, py, pw, ph, cx, cy, d, tile, sw, rng, L)


def _render_door(state, orient, px, py, pw, ph, cx, cy, d, tile, sw, rng, L):
    """Porta: stipiti + anta (closed/locked) o varco libero (open)."""
    if orient == 'h':
        # Stipiti verticali agli estremi
        L.append(f'<line x1="{px:.1f}" y1="{py:.1f}" x2="{px:.1f}" y2="{py+d:.1f}" stroke="black" stroke-width="{sw}"/>')
        L.append(f'<line x1="{px+pw:.1f}" y1="{py:.1f}" x2="{px+pw:.1f}" y2="{py+d:.1f}" stroke="black" stroke-width="{sw}"/>')
        L.append(f'<line x1="{px:.1f}" y1="{py+ph:.1f}" x2="{px:.1f}" y2="{py+ph-d:.1f}" stroke="black" stroke-width="{sw}"/>')
        L.append(f'<line x1="{px+pw:.1f}" y1="{py+ph:.1f}" x2="{px+pw:.1f}" y2="{py+ph-d:.1f}" stroke="black" stroke-width="{sw}"/>')
        if state in ('closed', 'locked'):
            # Anta orizzontale al centro
            j = rng.uniform(-0.5, 0.5)
            L.append(f'<line x1="{px+2:.1f}" y1="{cy+j:.1f}" x2="{px+pw-2:.1f}" y2="{cy+j:.1f}" stroke="black" stroke-width="{sw*1.2}"/>')
    else:
        L.append(f'<line x1="{px:.1f}" y1="{py:.1f}" x2="{px+d:.1f}" y2="{py:.1f}" stroke="black" stroke-width="{sw}"/>')
        L.append(f'<line x1="{px:.1f}" y1="{py+ph:.1f}" x2="{px+d:.1f}" y2="{py+ph:.1f}" stroke="black" stroke-width="{sw}"/>')
        L.append(f'<line x1="{px+pw:.1f}" y1="{py:.1f}" x2="{px+pw-d:.1f}" y2="{py:.1f}" stroke="black" stroke-width="{sw}"/>')
        L.append(f'<line x1="{px+pw:.1f}" y1="{py+ph:.1f}" x2="{px+pw-d:.1f}" y2="{py+ph:.1f}" stroke="black" stroke-width="{sw}"/>')
        if state in ('closed', 'locked'):
            j = rng.uniform(-0.5, 0.5)
            L.append(f'<line x1="{cx+j:.1f}" y1="{py+2:.1f}" x2="{cx+j:.1f}" y2="{py+ph-2:.1f}" stroke="black" stroke-width="{sw*1.2}"/>')

    if state == 'locked':
        # Lucchetto: piccolo cerchio sull'anta
        r = max(1.5, tile//10)
        L.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r}" fill="white" stroke="black" stroke-width="0.8"/>')
        L.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r*0.4:.1f}" fill="black"/>')


def _render_portcullis(state, orient, px, py, pw, ph, cx, cy, d, tile, sw, rng, L):
    """Saracinesca: griglia di sbarre."""
    bar_sw = max(1, tile//8)
    spacing = max(3, tile//4)
    if orient == 'h':
        # Sbarre verticali
        x = px + spacing
        while x < px + pw:
            j = rng.uniform(-0.3, 0.3)
            L.append(f'<line x1="{x+j:.1f}" y1="{py:.1f}" x2="{x+j:.1f}" y2="{py+ph:.1f}" stroke="black" stroke-width="{bar_sw}"/>')
            x += spacing
        if state == 'closed':
            # Sbarra orizzontale trasversale
            L.append(f'<line x1="{px:.1f}" y1="{cy:.1f}" x2="{px+pw:.1f}" y2="{cy:.1f}" stroke="black" stroke-width="{bar_sw}"/>')
    else:
        y = py + spacing
        while y < py + ph:
            j = rng.uniform(-0.3, 0.3)
            L.append(f'<line x1="{px:.1f}" y1="{y+j:.1f}" x2="{px+pw:.1f}" y2="{y+j:.1f}" stroke="black" stroke-width="{bar_sw}"/>')
            y += spacing
        if state == 'closed':
            L.append(f'<line x1="{cx:.1f}" y1="{py:.1f}" x2="{cx:.1f}" y2="{py+ph:.1f}" stroke="black" stroke-width="{bar_sw}"/>')


def _render_arch(orient, px, py, pw, ph, cx, cy, d, tile, sw, rng, L):
    """Arco: semicerchio sul varco."""
    if orient == 'h':
        r = pw / 2
        # Arco superiore
        L.append(f'<path d="M {px:.1f},{cy:.1f} Q {cx:.1f},{py:.1f} {px+pw:.1f},{cy:.1f}" stroke="black" stroke-width="{sw}" fill="none"/>')
        # Arco inferiore
        L.append(f'<path d="M {px:.1f},{cy:.1f} Q {cx:.1f},{py+ph:.1f} {px+pw:.1f},{cy:.1f}" stroke="black" stroke-width="{sw}" fill="none"/>')
    else:
        L.append(f'<path d="M {cx:.1f},{py:.1f} Q {px:.1f},{cy:.1f} {cx:.1f},{py+ph:.1f}" stroke="black" stroke-width="{sw}" fill="none"/>')
        L.append(f'<path d="M {cx:.1f},{py:.1f} Q {px+pw:.1f},{cy:.1f} {cx:.1f},{py+ph:.1f}" stroke="black" stroke-width="{sw}" fill="none"/>')


def _render_secret(state, orient, px, py, pw, ph, cx, cy, d, tile, sw, rng, L):
    """Porta segreta: hidden = muro normale (niente), found = tratteggio."""
    if state == 'found':
        # Tratteggio sottile a indicare il varco nascosto
        if orient == 'h':
            L.append(f'<line x1="{px:.1f}" y1="{cy:.1f}" x2="{px+pw:.1f}" y2="{cy:.1f}" stroke="black" stroke-width="0.6" stroke-dasharray="2,3"/>')
        else:
            L.append(f'<line x1="{cx:.1f}" y1="{py:.1f}" x2="{cx:.1f}" y2="{py+ph:.1f}" stroke="black" stroke-width="0.6" stroke-dasharray="2,3"/>')
    # hidden: non disegna nulla (il passage viene già reso come muro)
