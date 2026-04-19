"""Plugin OLDSCHOOL: reading_table (tavolo da lettura 2×2) — stile mano libera."""
import random


def _j(x1, y1, x2, y2, rng, amp=0.6):
    mx = x1 + (x2-x1)*0.5 + rng.uniform(-amp, amp)
    my = y1 + (y2-y1)*0.5 + rng.uniform(-amp, amp)
    return f'M {x1:.1f},{y1:.1f} L {mx:.1f},{my:.1f} L {x2:.1f},{y2:.1f}'


def render(obj, tpl, ox, oy, ow, oh, tile, L):
    rng = random.Random(hash((ox, oy)))

    def path(x1, y1, x2, y2, w=1.0):
        return f'<path d="{_j(x1,y1,x2,y2,rng)}" stroke="black" stroke-width="{w}" fill="none"/>'

    # Piano tavolo
    L.append(f'<rect x="{ox+1}" y="{oy+1}" width="{ow-2}" height="{oh-2}" fill="#d4b483" stroke="none"/>')
    L.append(path(ox+1, oy+1, ox+ow-1, oy+1))
    L.append(path(ox+ow-1, oy+1, ox+ow-1, oy+oh-1))
    L.append(path(ox+ow-1, oy+oh-1, ox+1, oy+oh-1))
    L.append(path(ox+1, oy+oh-1, ox+1, oy+1))
    # Libro aperto al centro
    cx, cy = ox + ow//2, oy + oh//2
    bw, bh = max(4, ow//3), max(3, oh//4)
    L.append(f'<rect x="{cx-bw:.0f}" y="{cy-bh:.0f}" width="{bw*2:.0f}" height="{bh*2:.0f}" fill="#f5f0e0" stroke="black" stroke-width="0.6"/>')
    L.append(path(cx, cy-bh, cx, cy+bh, w=0.5))
    # Righine testo
    for i in range(1, 3):
        ry2 = cy - bh + i * (bh*2//3)
        L.append(f'<line x1="{cx-bw+2:.0f}" y1="{ry2:.0f}" x2="{cx-2:.0f}" y2="{ry2:.0f}" stroke="#888" stroke-width="0.4"/>')
        L.append(f'<line x1="{cx+2:.0f}" y1="{ry2:.0f}" x2="{cx+bw-2:.0f}" y2="{ry2:.0f}" stroke="#888" stroke-width="0.4"/>')
