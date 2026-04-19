"""Plugin OLDSCHOOL: table e large_table — stile mano libera."""
import random

_clip_id = 0


def _jline(x1, y1, x2, y2, rng, amp=0.7, segs=3):
    pts = [(x1, y1)]
    for i in range(1, segs):
        t = i / segs
        pts.append((x1+(x2-x1)*t + rng.uniform(-amp, amp),
                    y1+(y2-y1)*t + rng.uniform(-amp, amp)))
    pts.append((x2, y2))
    return 'M ' + ' L '.join(f'{p[0]:.1f},{p[1]:.1f}' for p in pts)


def render(obj, tpl, ox, oy, ow, oh, tile, L):
    cid = f'tbl_{ox}_{oy}'

    rng = random.Random(hash((ox, oy)))
    leg = max(3, tile // 5)
    r_leg = max(4, leg)
    sw = 1.0

    tx0, ty0 = ox + leg, oy + leg
    tx1, ty1 = ox + ow - leg, oy + oh - leg
    pw, ph = tx1 - tx0, ty1 - ty0
    corners = [(tx0, ty0), (tx1, ty0), (tx0, ty1), (tx1, ty1)]

    # 1. Gambe (sotto il fill)
    for lx, ly in corners:
        L.append(f'<circle cx="{lx}" cy="{ly}" r="{r_leg}" fill="black"/>')

    # 2. Fill grigio + diagonali clippati nel piano
    L.append(f'<defs><clipPath id="{cid}"><rect x="{tx0}" y="{ty0}" width="{pw}" height="{ph}"/></clipPath></defs>')
    L.append(f'<g clip-path="url(#{cid})">')
    L.append(f'<rect x="{tx0}" y="{ty0}" width="{pw}" height="{ph}" fill="#e8e8e8" stroke="none"/>')
    spacing = max(6, tile // 3)
    for off in range(-ph, pw+ph, spacing):
        x1 = tx0 + max(0, off);  y1 = ty0 + max(0, -off)
        x2 = tx0 + min(pw, off+ph); y2 = ty0 + min(ph, off+pw)
        if x2 > x1 and y2 > y1:
            L.append(f'<path d="{_jline(x1,y1,x2,y2,rng,amp=1.2,segs=3)}" stroke="#bbb" stroke-width="0.6" fill="none"/>')
    L.append('</g>')

    # 3. Bordo piano con jitter
    def path(x1, y1, x2, y2):
        return f'<path d="{_jline(x1,y1,x2,y2,rng,amp=0.8)}" stroke="black" stroke-width="{sw}" fill="none"/>'
    L.append(path(tx0, ty0, tx1, ty0))
    L.append(path(tx1, ty0, tx1, ty1))
    L.append(path(tx1, ty1, tx0, ty1))
    L.append(path(tx0, ty1, tx0, ty0))
