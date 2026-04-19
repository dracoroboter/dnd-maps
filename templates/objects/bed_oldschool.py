"""Plugin OLDSCHOOL: bed (letto 1×2, direzionale) — stile mano libera."""
import random


def _jline(x1, y1, x2, y2, rng, amp=1.0, segs=4):
    pts = [(x1, y1)]
    for i in range(1, segs):
        t = i / segs
        pts.append((x1+(x2-x1)*t + rng.uniform(-amp, amp),
                    y1+(y2-y1)*t + rng.uniform(-amp, amp)))
    pts.append((x2, y2))
    return 'M ' + ' L '.join(f'{p[0]:.1f},{p[1]:.1f}' for p in pts)


def render(obj, tpl, ox, oy, ow, oh, tile, L):
    direction = obj.get('direction', 'south')
    rng = random.Random(hash((ox, oy, direction)))
    sw = 1.2
    amp = 0.8
    j = rng.uniform

    def path(x1, y1, x2, y2):
        return f'<path d="{_jline(x1,y1,x2,y2,rng,amp)}" stroke="black" stroke-width="{sw}" fill="none"/>'

    def pillow(px0, py0, px1, py1):
        """Rettangolo arrotondato con angoli e lati leggermente irregolari."""
        r = 3
        L.append(
            f'<path d="'
            f'M {px0+r+j(-0.8,0.8):.1f},{py0+j(-0.5,0.5):.1f} '
            f'L {px1-r+j(-0.8,0.8):.1f},{py0+j(-0.5,0.5):.1f} '
            f'Q {px1+j(-0.5,0.5):.1f},{py0+j(-0.5,0.5):.1f} {px1+j(-0.5,0.5):.1f},{py0+r+j(-0.8,0.8):.1f} '
            f'L {px1+j(-0.5,0.5):.1f},{py1-r+j(-0.8,0.8):.1f} '
            f'Q {px1+j(-0.5,0.5):.1f},{py1+j(-0.5,0.5):.1f} {px1-r+j(-0.8,0.8):.1f},{py1+j(-0.5,0.5):.1f} '
            f'L {px0+r+j(-0.8,0.8):.1f},{py1+j(-0.5,0.5):.1f} '
            f'Q {px0+j(-0.5,0.5):.1f},{py1+j(-0.5,0.5):.1f} {px0+j(-0.5,0.5):.1f},{py1-r+j(-0.8,0.8):.1f} '
            f'L {px0+j(-0.5,0.5):.1f},{py0+r+j(-0.8,0.8):.1f} '
            f'Q {px0+j(-0.5,0.5):.1f},{py0+j(-0.5,0.5):.1f} {px0+r+j(-0.8,0.8):.1f},{py0+j(-0.5,0.5):.1f} Z" '
            f'stroke="black" stroke-width="0.8" fill="none"/>'
        )

    # Bordo esterno con fill grigio chiaro
    L.append(f'<rect x="{ox}" y="{oy}" width="{ow}" height="{oh}" fill="#e8e8e8" stroke="none"/>')
    L.append(path(ox,    oy,    ox+ow, oy))
    L.append(path(ox+ow, oy,    ox+ow, oy+oh))
    L.append(path(ox+ow, oy+oh, ox,    oy+oh))
    L.append(path(ox,    oy+oh, ox,    oy))

    mg = max(2, tile // 8)

    if direction in ('north', 'south'):
        mid = oh // 3
        ly = oy + mid if direction == 'north' else oy + oh - mid
        L.append(path(ox, ly, ox+ow, ly))
        py0 = oy + mg if direction == 'north' else oy + oh - mid + mg
        py1 = oy + mid - mg if direction == 'north' else oy + oh - mg
        pillow(ox + mg, py0, ox + ow - mg, py1)
        # Lenzuolo (area corpo)
        bx0, bx1 = ox + mg, ox + ow - mg
        by0 = oy + mid + mg if direction == 'north' else oy + mg
        by1 = oy + oh - mg if direction == 'north' else oy + oh - mid - mg
    else:
        mid = ow // 3
        lx = ox + mid if direction == 'west' else ox + ow - mid
        L.append(path(lx, oy, lx, oy+oh))
        px0 = ox + mg if direction == 'west' else ox + ow - mid + mg
        px1 = ox + mid - mg if direction == 'west' else ox + ow - mg
        pillow(px0, oy + mg, px1, oy + oh - mg)
        bx0 = ox + mid + mg if direction == 'west' else ox + mg
        bx1 = ox + ow - mg if direction == 'west' else ox + ow - mid - mg
        by0, by1 = oy + mg, oy + oh - mg

    # Puntini lenzuolo se sheet_type == 'dots'
    if obj.get('sheet_type', 'plain') == 'dots':
        spacing = max(3, tile // 5)
        xs = [bx0 + spacing//2 + i*spacing for i in range(int((bx1-bx0)/spacing))]
        ys = [by0 + spacing//2 + i*spacing for i in range(int((by1-by0)/spacing))]
        for dx in xs:
            for dy in ys:
                jx = rng.uniform(-0.6, 0.6)
                jy = rng.uniform(-0.6, 0.6)
                L.append(f'<circle cx="{dx+jx:.1f}" cy="{dy+jy:.1f}" r="0.8" fill="black"/>')
