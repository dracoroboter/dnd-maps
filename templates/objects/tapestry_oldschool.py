"""Plugin OLDSCHOOL: tapestry (arazzo 1×2, direzionale) — stile mano libera."""
import random


def render(obj, tpl, ox, oy, ow, oh, tile, L):
    rng = random.Random(hash((ox, oy)))
    m = max(1, tile // 10)

    colors = ['#8b1a1a', '#1a1a8b', '#1a6b1a', '#6b1a6b']
    bg = rng.choice(colors)

    # Sfondo arazzo
    L.append(f'<rect x="{ox}" y="{oy}" width="{ow}" height="{oh}" fill="{bg}" stroke="black" stroke-width="1.2"/>')

    # Bordo decorativo interno
    L.append(f'<rect x="{ox+m}" y="{oy+m}" width="{ow-2*m}" height="{oh-2*m}" '
             f'fill="none" stroke="#d4a830" stroke-width="{max(0.5,m*0.6):.1f}"/>')

    # Motivo centrale (rombo)
    cx, cy = ox + ow/2, oy + oh/2
    rw, rh = ow*0.28, oh*0.22
    pts = [
        f'{cx:.1f},{cy-rh:.1f}',
        f'{cx+rw:.1f},{cy:.1f}',
        f'{cx:.1f},{cy+rh:.1f}',
        f'{cx-rw:.1f},{cy:.1f}',
    ]
    L.append(f'<polygon points="{" ".join(pts)}" fill="#d4a830" stroke="none" opacity="0.7"/>')

    # Frangia in basso
    fringe_n = max(3, ow // (tile//4))
    fw = ow / fringe_n
    for i in range(fringe_n):
        fx = ox + i * fw + fw/2
        jx = fx + rng.uniform(-fw*0.15, fw*0.15)
        L.append(f'<line x1="{jx:.1f}" y1="{oy+oh:.1f}" x2="{jx:.1f}" y2="{oy+oh+max(2,tile//5):.1f}" '
                 f'stroke="#d4a830" stroke-width="0.8"/>')
