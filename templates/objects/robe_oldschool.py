"""Plugin OLDSCHOOL: robe (tunica appesa 1×1) — stile mano libera."""
import random


def _j(x1, y1, x2, y2, rng, amp=0.5):
    mx = x1 + (x2 - x1) * 0.5 + rng.uniform(-amp, amp)
    my = y1 + (y2 - y1) * 0.5 + rng.uniform(-amp, amp)
    return f'M {x1:.1f},{y1:.1f} L {mx:.1f},{my:.1f} L {x2:.1f},{y2:.1f}'


def render(obj, tpl, ox, oy, ow, oh, tile, L):
    rng = random.Random(hash((ox, oy)))
    cx = ox + ow / 2
    top = oy + oh * 0.1
    bot = oy + oh * 0.92
    shoulder_w = ow * 0.72
    hem_w = ow * 0.55
    neck_w = ow * 0.18

    # Sagoma tunica (path a forma di abito)
    sx = cx - shoulder_w / 2
    ex = cx + shoulder_w / 2
    hx = cx - hem_w / 2
    hx2 = cx + hem_w / 2
    nx = cx - neck_w / 2
    nx2 = cx + neck_w / 2

    jamp = max(0.4, tile * 0.03)

    def jp(x, y):
        return x + rng.uniform(-jamp, jamp), y + rng.uniform(-jamp, jamp)

    pts = [jp(nx, top), jp(ex, top + oh * 0.06), jp(hx2, bot),
           jp(hx, bot), jp(sx, top + oh * 0.06), jp(nx2, top)]
    d = 'M ' + ' L '.join(f'{p[0]:.1f},{p[1]:.1f}' for p in pts) + ' Z'
    L.append(f'<path d="{d}" fill="#1a1a2e" stroke="black" stroke-width="1" opacity="0.85"/>')

    # Linea centrale (apertura frontale)
    L.append(f'<path d="{_j(cx, top+oh*0.06, cx, bot-oh*0.05, rng, amp=jamp*0.5)}" '
             f'stroke="#555" stroke-width="0.7" fill="none"/>')

    # Gancio/appendino in cima
    L.append(f'<line x1="{cx:.1f}" y1="{oy:.1f}" x2="{cx:.1f}" y2="{top:.1f}" '
             f'stroke="black" stroke-width="1.2"/>')
    L.append(f'<circle cx="{cx:.1f}" cy="{oy:.1f}" r="{max(1.5, tile*0.07):.1f}" '
             f'fill="none" stroke="black" stroke-width="1"/>')
