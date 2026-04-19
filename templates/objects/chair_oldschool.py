"""Plugin OLDSCHOOL: chair (sedia 1×1) — stile mano libera."""
import random


def render(obj, tpl, ox, oy, ow, oh, tile, L):
    rng = random.Random(hash((ox, oy)))
    m = max(2, tile // 6)
    cx, cy = ox + ow//2, oy + oh//2

    def jp(x, y):
        return x + rng.uniform(-0.5, 0.5), y + rng.uniform(-0.5, 0.5)

    # Seduta
    sx1, sy1 = ox + m, oy + m + oh//5
    sx2, sy2 = ox + ow - m, oy + oh - m
    pts = [jp(sx1, sy1), jp(sx2, sy1), jp(sx2, sy2), jp(sx1, sy2)]
    d = 'M ' + ' L '.join(f'{p[0]:.1f},{p[1]:.1f}' for p in pts) + ' Z'
    L.append(f'<path d="{d}" fill="#c8a870" stroke="black" stroke-width="0.8"/>')

    # Schienale (rettangolo sottile in alto)
    bx1, by1 = ox + m, oy + m
    bx2, by2 = ox + ow - m, oy + m + oh//5
    pts2 = [jp(bx1, by1), jp(bx2, by1), jp(bx2, by2), jp(bx1, by2)]
    d2 = 'M ' + ' L '.join(f'{p[0]:.1f},{p[1]:.1f}' for p in pts2) + ' Z'
    L.append(f'<path d="{d2}" fill="#a07840" stroke="black" stroke-width="0.8"/>')
