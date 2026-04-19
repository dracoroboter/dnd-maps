"""Plugin OLDSCHOOL: weapon_rack (rastrelliera armi 1×2, direzionale) — stile mano libera."""
import random, math


def render(obj, tpl, ox, oy, ow, oh, tile, L):
    rng = random.Random(hash((ox, oy)))

    # Struttura rastrelliera (rettangolo con sbarre orizzontali)
    L.append(f'<rect x="{ox}" y="{oy}" width="{ow}" height="{oh}" fill="#c8b880" stroke="black" stroke-width="1"/>')

    # Sbarre orizzontali della rastrelliera
    n_bars = max(2, oh // (tile//3)) if oh > ow else max(2, ow // (tile//3))
    if oh >= ow:
        for i in range(1, n_bars):
            by = oy + i * oh // n_bars
            bx = by + rng.uniform(-0.4, 0.4)
            L.append(f'<line x1="{ox+1:.0f}" y1="{by:.1f}" x2="{ox+ow-1:.0f}" y2="{by:.1f}" '
                     f'stroke="#6b5020" stroke-width="0.8"/>')
    else:
        for i in range(1, n_bars):
            bx = ox + i * ow // n_bars
            L.append(f'<line x1="{bx:.1f}" y1="{oy+1:.0f}" x2="{bx:.1f}" y2="{oy+oh-1:.0f}" '
                     f'stroke="#6b5020" stroke-width="0.8"/>')

    # Armi stilizzate: spade (linee diagonali)
    n_weapons = rng.randint(2, 4)
    for i in range(n_weapons):
        if oh >= ow:
            wx = ox + ow/2 + rng.uniform(-ow*0.25, ow*0.25)
            wy1 = oy + (i + 0.3) * oh / n_weapons
            wy2 = oy + (i + 0.7) * oh / n_weapons
            angle = rng.uniform(-0.3, 0.3)
            dx = (wy2-wy1)*math.sin(angle)
            L.append(f'<line x1="{wx-dx:.1f}" y1="{wy1:.1f}" x2="{wx+dx:.1f}" y2="{wy2:.1f}" '
                     f'stroke="#444" stroke-width="1.2"/>')
        else:
            wy = oy + oh/2 + rng.uniform(-oh*0.25, oh*0.25)
            wx1 = ox + (i + 0.3) * ow / n_weapons
            wx2 = ox + (i + 0.7) * ow / n_weapons
            L.append(f'<line x1="{wx1:.1f}" y1="{wy:.1f}" x2="{wx2:.1f}" y2="{wy:.1f}" '
                     f'stroke="#444" stroke-width="1.2"/>')
