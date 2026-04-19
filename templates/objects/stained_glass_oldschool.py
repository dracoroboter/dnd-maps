"""Plugin OLDSCHOOL: stained_glass (vetrata 2×1, direzionale) — stile mano libera."""
import random


def _j(x1, y1, x2, y2, rng, amp=0.5):
    mx = x1 + (x2 - x1) * 0.5 + rng.uniform(-amp, amp)
    my = y1 + (y2 - y1) * 0.5 + rng.uniform(-amp, amp)
    return f'M {x1:.1f},{y1:.1f} L {mx:.1f},{my:.1f} L {x2:.1f},{y2:.1f}'


def render(obj, tpl, ox, oy, ow, oh, tile, L):
    rng = random.Random(hash((ox, oy)))
    m = max(2, tile // 8)  # margine interno

    # Sfondo piombo
    L.append(f'<rect x="{ox}" y="{oy}" width="{ow}" height="{oh}" '
             f'fill="#2a2a2a" stroke="black" stroke-width="1.2"/>')

    # Suddividi la vetrata in pannelli colorati
    panels = [
        ('#7ec8e3', '#4a90c4'),  # blu
        ('#e8c97a', '#c8960a'),  # oro
        ('#a0d080', '#5a9040'),  # verde
        ('#e07070', '#b03030'),  # rosso
    ]

    cx, cy = ox + ow / 2, oy + oh / 2

    if ow >= oh:
        # Orientamento orizzontale: 2 pannelli affiancati + arco in cima
        pw = (ow - 3 * m) / 2
        ph = oh - 2 * m
        for i, (fill, stroke) in enumerate(panels[:2]):
            px = ox + m + i * (pw + m)
            py = oy + m
            arc_rx, arc_ry = pw / 2, min(ph * 0.3, tile * 0.4)
            flat_h = ph - arc_ry
            L.append(
                f'<path d="M {px:.1f},{py+arc_ry:.1f} '
                f'Q {px+pw/2:.1f},{py:.1f} {px+pw:.1f},{py+arc_ry:.1f} '
                f'L {px+pw:.1f},{py+ph:.1f} L {px:.1f},{py+ph:.1f} Z" '
                f'fill="{fill}" stroke="{stroke}" stroke-width="0.8" opacity="0.85"/>'
            )
    else:
        # Orientamento verticale: 2 pannelli impilati + arco in cima
        pw = ow - 2 * m
        ph = (oh - 3 * m) / 2
        for i, (fill, stroke) in enumerate(panels[:2]):
            px = ox + m
            py = oy + m + i * (ph + m)
            if i == 0:
                arc_ry = min(ph * 0.3, tile * 0.4)
                L.append(
                    f'<path d="M {px:.1f},{py+arc_ry:.1f} '
                    f'Q {px+pw/2:.1f},{py:.1f} {px+pw:.1f},{py+arc_ry:.1f} '
                    f'L {px+pw:.1f},{py+ph:.1f} L {px:.1f},{py+ph:.1f} Z" '
                    f'fill="{fill}" stroke="{stroke}" stroke-width="0.8" opacity="0.85"/>'
                )
            else:
                L.append(
                    f'<rect x="{px:.1f}" y="{py:.1f}" width="{pw:.1f}" height="{ph:.1f}" '
                    f'fill="{fill}" stroke="{stroke}" stroke-width="0.8" opacity="0.85"/>'
                )

    # Piombo divisorio centrale (linea jitterata)
    if ow >= oh:
        mx2 = ox + ow / 2
        L.append(f'<path d="{_j(mx2, oy+m, mx2, oy+oh-m, rng)}" '
                 f'stroke="#1a1a1a" stroke-width="1.5" fill="none"/>')
    else:
        my2 = oy + oh / 2
        L.append(f'<path d="{_j(ox+m, my2, ox+ow-m, my2, rng)}" '
                 f'stroke="#1a1a1a" stroke-width="1.5" fill="none"/>')

    # Bordo esterno
    L.append(f'<rect x="{ox}" y="{oy}" width="{ow}" height="{oh}" '
             f'fill="none" stroke="black" stroke-width="1.5"/>')
