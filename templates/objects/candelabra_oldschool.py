"""Plugin OLDSCHOOL: candelabra (candelabro 1×1) — stile mano libera."""
import random, math


def render(obj, tpl, ox, oy, ow, oh, tile, L):
    rng = random.Random(hash((ox, oy)))
    cx, cy = ox + ow / 2, oy + oh / 2
    base_r = max(2.5, tile * 0.18)
    stem_h = oh * 0.45

    def jpt(x, y, amp=0.6):
        return x + rng.uniform(-amp, amp), y + rng.uniform(-amp, amp)

    def line(x1, y1, x2, y2, w=1.0):
        jx1, jy1 = jpt(x1, y1)
        jx2, jy2 = jpt(x2, y2)
        L.append(f'<line x1="{jx1:.1f}" y1="{jy1:.1f}" x2="{jx2:.1f}" y2="{jy2:.1f}" '
                 f'stroke="black" stroke-width="{w}" fill="none"/>')

    # Base ovale
    L.append(f'<ellipse cx="{cx:.1f}" cy="{cy+stem_h/2:.1f}" '
             f'rx="{base_r:.1f}" ry="{base_r*0.4:.1f}" '
             f'fill="#c8c8c8" stroke="black" stroke-width="0.8"/>')

    # Fusto verticale
    line(cx, cy + stem_h / 2 - 1, cx, cy - stem_h / 2, w=1.2)

    # Bracci laterali (candelabro a 3 candele)
    arm_y = cy - stem_h * 0.1
    arm_x = ow * 0.28
    for dx in (-arm_x, 0, arm_x):
        tip_x, tip_y = cx + dx, cy - stem_h / 2 - oh * 0.04
        if dx != 0:
            line(cx, arm_y, cx + dx, arm_y, w=0.8)
            line(cx + dx, arm_y, cx + dx, tip_y, w=0.8)
        # Fiamma
        fx, fy = tip_x + rng.uniform(-0.4, 0.4), tip_y
        flame_h = max(3, tile * 0.14)
        L.append(f'<ellipse cx="{fx:.1f}" cy="{fy - flame_h/2:.1f}" '
                 f'rx="{max(1.5, flame_h*0.4):.1f}" ry="{flame_h/2:.1f}" '
                 f'fill="#f5a623" stroke="#c07000" stroke-width="0.5" opacity="0.9"/>')
