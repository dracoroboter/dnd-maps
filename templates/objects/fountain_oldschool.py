"""Plugin OLDSCHOOL: fountain e large_fountain — stile mano libera."""
import random, math


def _jcirc(cx, cy, r, rng, amp=0.8, step=12):
    pts = []
    for a in range(0, 360, step):
        rad = math.radians(a)
        jr = r + rng.uniform(-amp, amp)
        pts.append(f'{cx+jr*math.cos(rad):.1f},{cy+jr*math.sin(rad):.1f}')
    return f'<polygon points="{" ".join(pts)}" '


def render(obj, tpl, ox, oy, ow, oh, tile, L):
    rng = random.Random(hash((ox, oy)))
    cx, cy = ox + ow/2, oy + oh/2
    r_outer = min(ow, oh)/2 * 0.82
    r_inner = r_outer * 0.45
    r_jet   = r_inner * 0.35

    # Vasca esterna
    L.append(_jcirc(cx, cy, r_outer, rng, amp=1.0) + 'fill="#e8e8e8" stroke="black" stroke-width="1.2"/>')
    # Bordo vasca (secondo cerchio leggermente più piccolo)
    L.append(_jcirc(cx, cy, r_outer*0.88, rng, amp=0.6) + 'fill="none" stroke="black" stroke-width="0.6"/>')
    # Piedistallo centrale
    L.append(_jcirc(cx, cy, r_inner, rng, amp=0.5) + 'fill="white" stroke="black" stroke-width="1.0"/>')
    # Zampillo: 4 linee curve verso l'esterno
    for i in range(4):
        a = math.radians(45 + i*90)
        jx, jy = rng.uniform(-0.5,0.5), rng.uniform(-0.5,0.5)
        x1, y1 = cx + jx, cy + jy
        x2 = cx + r_inner*0.7*math.cos(a) + jx
        y2 = cy + r_inner*0.7*math.sin(a) + jy
        L.append(f'<path d="M {x1:.1f},{y1:.1f} Q {x2:.1f},{y2:.1f} {x2+rng.uniform(-1,1):.1f},{y2+rng.uniform(-1,1):.1f}" stroke="black" stroke-width="0.7" fill="none"/>')
    # Punto centrale
    L.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r_jet:.1f}" fill="black"/>')
