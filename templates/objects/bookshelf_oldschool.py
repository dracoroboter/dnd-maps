"""Plugin OLDSCHOOL: bookshelf (libreria 1×2, direzionale) — stile mano libera."""
import random


def _j(x1, y1, x2, y2, rng, amp=0.6):
    pts = [(x1, y1), (x1+(x2-x1)*0.5+rng.uniform(-amp,amp), y1+(y2-y1)*0.5+rng.uniform(-amp,amp)), (x2, y2)]
    return 'M ' + ' L '.join(f'{p[0]:.1f},{p[1]:.1f}' for p in pts)


def render(obj, tpl, ox, oy, ow, oh, tile, L):
    rng = random.Random(hash((ox, oy)))

    def path(x1, y1, x2, y2, amp=0.6, w=1.0):
        return f'<path d="{_j(x1,y1,x2,y2,rng,amp)}" stroke="black" stroke-width="{w}" fill="none"/>'

    # Fill
    L.append(f'<rect x="{ox}" y="{oy}" width="{ow}" height="{oh}" fill="#e8e8e8" stroke="none"/>')
    # Bordo
    L.append(path(ox, oy, ox+ow, oy))
    L.append(path(ox+ow, oy, ox+ow, oy+oh))
    L.append(path(ox+ow, oy+oh, ox, oy+oh))
    L.append(path(ox, oy+oh, ox, oy))
    # Divisori libri (verticali o orizzontali secondo orientamento)
    if ow >= oh:  # orizzontale
        n = max(2, ow // (tile // 3))
        bw = ow / n
        for i in range(1, n):
            bx = ox + i * bw
            L.append(path(bx, oy+2, bx, oy+oh-2, amp=0.4, w=0.7))
    else:  # verticale
        n = max(2, oh // (tile // 3))
        bh = oh / n
        for i in range(1, n):
            by = oy + i * bh
            L.append(path(ox+2, by, ox+ow-2, by, amp=0.4, w=0.7))
