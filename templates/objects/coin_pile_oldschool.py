"""Plugin OLDSCHOOL: coin_pile (pila di monete 4×4) — stile mano libera."""
import random, math


def render(obj, tpl, ox, oy, ow, oh, tile, L):
    rng = random.Random(hash((ox, oy)))
    cx, cy = ox + ow / 2, oy + oh / 2
    r_heap = min(ow, oh) * 0.42

    # Ombra della pila
    L.append(
        f'<ellipse cx="{cx+2:.1f}" cy="{cy+3:.1f}" '
        f'rx="{r_heap*1.05:.1f}" ry="{r_heap*0.55:.1f}" '
        f'fill="#bbb" opacity="0.4"/>'
    )

    # Sagoma della pila (ellisse piena dorata)
    pts = []
    for a in range(0, 360, 10):
        rad = math.radians(a)
        jr = r_heap + rng.uniform(-r_heap * 0.08, r_heap * 0.08)
        pts.append(
            f'{cx + jr * math.cos(rad):.1f},'
            f'{cy + jr * math.sin(rad) * 0.6:.1f}'
        )
    L.append(
        f'<polygon points="{" ".join(pts)}" '
        f'fill="#d4a017" stroke="#8b6000" stroke-width="1"/>'
    )

    # Monete sparse: piccoli cerchi sovrapposti
    n_coins = int(r_heap * 0.9)
    for _ in range(n_coins):
        angle = rng.uniform(0, 2 * math.pi)
        dist  = rng.uniform(0, r_heap * 0.75)
        ccx   = cx + dist * math.cos(angle)
        ccy   = cy + dist * math.sin(angle) * 0.6
        cr    = max(2.5, tile * 0.12) + rng.uniform(-0.5, 0.5)
        fill  = rng.choice(['#f5c842', '#e6b800', '#ffd700', '#c8a800'])
        L.append(
            f'<ellipse cx="{ccx:.1f}" cy="{ccy:.1f}" '
            f'rx="{cr:.1f}" ry="{cr*0.65:.1f}" '
            f'fill="{fill}" stroke="#8b6000" stroke-width="0.5" opacity="0.85"/>'
        )

    # Contorno finale
    L.append(
        f'<polygon points="{" ".join(pts)}" '
        f'fill="none" stroke="#5a3e00" stroke-width="1.2"/>'
    )
