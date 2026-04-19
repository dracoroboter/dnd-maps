"""Plugin OLDSCHOOL: altar (altare 2×1) — stile mano libera."""
import random


def _j(x1, y1, x2, y2, rng, amp=0.7):
    pts = [(x1, y1), (x1+(x2-x1)*0.5+rng.uniform(-amp,amp), y1+(y2-y1)*0.5+rng.uniform(-amp,amp)), (x2, y2)]
    return 'M ' + ' L '.join(f'{p[0]:.1f},{p[1]:.1f}' for p in pts)


def render(obj, tpl, ox, oy, ow, oh, tile, L):
    rng = random.Random(hash((ox, oy)))
    cx, cy = ox + ow // 2, oy + oh // 2

    def path(x1, y1, x2, y2, amp=0.7):
        return f'<path d="{_j(x1,y1,x2,y2,rng,amp)}" stroke="black" stroke-width="1" fill="none"/>'

    # Fill
    L.append(f'<rect x="{ox+1}" y="{oy+1}" width="{ow-2}" height="{oh-2}" fill="#e8e8e8" stroke="none"/>')
    # Bordo
    L.append(path(ox+1, oy+1, ox+ow-1, oy+1))
    L.append(path(ox+ow-1, oy+1, ox+ow-1, oy+oh-1))
    L.append(path(ox+ow-1, oy+oh-1, ox+1, oy+oh-1))
    L.append(path(ox+1, oy+oh-1, ox+1, oy+1))
    # Croce
    L.append(path(cx, oy+3, cx, oy+oh-3, amp=0.5))
    L.append(path(ox+3, oy+oh//3, ox+ow-3, oy+oh//3, amp=0.5))
