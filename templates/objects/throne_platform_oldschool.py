"""Plugin OLDSCHOOL: throne_platform (pedana trono 4×3) — stile mano libera."""
import random


def _j(x1, y1, x2, y2, rng, amp=0.7):
    mx = x1+(x2-x1)*0.5+rng.uniform(-amp, amp)
    my = y1+(y2-y1)*0.5+rng.uniform(-amp, amp)
    return f'M {x1:.1f},{y1:.1f} L {mx:.1f},{my:.1f} L {x2:.1f},{y2:.1f}'


def render(obj, tpl, ox, oy, ow, oh, tile, L):
    rng = random.Random(hash((ox, oy)))

    def path(x1, y1, x2, y2, w=1.0, col="black"):
        return f'<path d="{_j(x1,y1,x2,y2,rng)}" stroke="{col}" stroke-width="{w}" fill="none"/>'

    # Determine facing direction from object
    direction = obj.get('direction', 'north')

    # Pedana (gradini): 3 bordi concentrici verso il fronte
    step = max(2, min(tile//5, ow//8, oh//6))
    for i in range(3):
        s = i * step
        L.append(f'<rect x="{ox+s:.0f}" y="{oy+s:.0f}" width="{ow-2*s:.0f}" height="{oh-2*s:.0f}" '
                 f'fill="#d0c090" stroke="black" stroke-width="{1.2-i*0.3:.1f}"/>')

    # Trono al centro della pedana (rettangolo più scuro)
    tw, th = max(tile, ow//3), max(tile, oh//3)
    tx = ox + (ow - tw)//2
    ty = oy + (oh - th)//2
    L.append(f'<rect x="{tx:.0f}" y="{ty:.0f}" width="{tw:.0f}" height="{th:.0f}" '
             f'fill="#8b6914" stroke="black" stroke-width="1.2"/>')

    # Schienale trono (banda più scura in cima al trono, verso il muro)
    back_h = max(3, th//3)
    if direction in ('north', 'west'):
        L.append(f'<rect x="{tx:.0f}" y="{ty:.0f}" width="{tw:.0f}" height="{back_h:.0f}" '
                 f'fill="#5a3e00" stroke="black" stroke-width="0.8"/>')
    else:
        L.append(f'<rect x="{tx:.0f}" y="{ty+th-back_h:.0f}" width="{tw:.0f}" height="{back_h:.0f}" '
                 f'fill="#5a3e00" stroke="black" stroke-width="0.8"/>')

    # Cornice esterna bordo pedana
    L.append(path(ox, oy, ox+ow, oy, w=1.5))
    L.append(path(ox+ow, oy, ox+ow, oy+oh, w=1.5))
    L.append(path(ox+ow, oy+oh, ox, oy+oh, w=1.5))
    L.append(path(ox, oy+oh, ox, oy, w=1.5))
