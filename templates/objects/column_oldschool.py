"""Plugin OLDSCHOOL: column (colonna 1×1) — stile mano libera."""
import random, math


def render(obj, tpl, ox, oy, ow, oh, tile, L):
    rng = random.Random(hash((ox, oy)))
    cx, cy = ox + ow // 2, oy + oh // 2
    r = max(3, tile * 2 // 5)

    # Cerchio esterno con jitter
    pts = []
    for a in range(0, 360, 15):
        rad = math.radians(a)
        jr = r + rng.uniform(-0.8, 0.8)
        pts.append(f'{cx+jr*math.cos(rad):.1f},{cy+jr*math.sin(rad):.1f}')
    L.append(f'<polygon points="{" ".join(pts)}" fill="#e8e8e8" stroke="black" stroke-width="1.5"/>')
    # Punto centrale
    L.append(f'<circle cx="{cx}" cy="{cy}" r="{max(1, r//3)}" fill="black"/>')
