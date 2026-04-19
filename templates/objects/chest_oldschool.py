"""Plugin OLDSCHOOL: chest (forziere 1×1) — stile mano libera."""
import random


def _j(x1, y1, x2, y2, rng, amp=0.7):
    pts = [(x1, y1), (x1+(x2-x1)*0.5+rng.uniform(-amp,amp), y1+(y2-y1)*0.5+rng.uniform(-amp,amp)), (x2, y2)]
    return 'M ' + ' L '.join(f'{p[0]:.1f},{p[1]:.1f}' for p in pts)


def render(obj, tpl, ox, oy, ow, oh, tile, L):
    rng = random.Random(hash((ox, oy)))
    cx = ox + ow // 2
    mid = oy + oh // 2

    def path(x1, y1, x2, y2):
        return f'<path d="{_j(x1,y1,x2,y2,rng)}" stroke="black" stroke-width="1" fill="none"/>'

    # Fill
    L.append(f'<rect x="{ox}" y="{oy}" width="{ow}" height="{oh}" fill="#e8e8e8" stroke="none"/>')
    # Bordo esterno
    L.append(path(ox, oy, ox+ow, oy))
    L.append(path(ox+ow, oy, ox+ow, oy+oh))
    L.append(path(ox+ow, oy+oh, ox, oy+oh))
    L.append(path(ox, oy+oh, ox, oy))
    # Linea coperchio
    L.append(path(ox, mid, ox+ow, mid))
    # Serratura
    L.append(f'<circle cx="{cx}" cy="{mid}" r="{max(1.5, tile//8)}" fill="black"/>')
