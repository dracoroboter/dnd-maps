"""Plugin OLDSCHOOL: mask (maschera rituale 1×1) — stile mano libera."""
import random, math


def render(obj, tpl, ox, oy, ow, oh, tile, L):
    rng = random.Random(hash((ox, oy)))
    cx, cy = ox + ow / 2, oy + oh / 2
    rw = ow * 0.38
    rh = oh * 0.46

    def jpt(x, y, amp=0.5):
        return x + rng.uniform(-amp, amp), y + rng.uniform(-amp, amp)

    # Contorno ovale della maschera con jitter
    pts = []
    for a in range(0, 360, 12):
        rad = math.radians(a)
        jrw = rw + rng.uniform(-rw * 0.07, rw * 0.07)
        jrh = rh + rng.uniform(-rh * 0.07, rh * 0.07)
        pts.append(f'{cx+jrw*math.cos(rad):.1f},{cy+jrh*math.sin(rad):.1f}')
    L.append(f'<polygon points="{" ".join(pts)}" fill="#3a2a1a" stroke="black" stroke-width="1.2"/>')

    # Occhi (due buchi ovali vuoti)
    eye_dx = rw * 0.38
    eye_dy = rh * 0.12
    eye_rx = max(1.5, rw * 0.22)
    eye_ry = max(1.2, rh * 0.16)
    for dx in (-eye_dx, eye_dx):
        ex, ey = jpt(cx + dx, cy - eye_dy, 0.4)
        L.append(f'<ellipse cx="{ex:.1f}" cy="{ey:.1f}" '
                 f'rx="{eye_rx:.1f}" ry="{eye_ry:.1f}" fill="#eee" stroke="black" stroke-width="0.7"/>')

    # Bocca (linea curva)
    mx1, my1 = jpt(cx - rw * 0.32, cy + rh * 0.28, 0.4)
    mx2, my2 = jpt(cx, cy + rh * 0.44, 0.4)
    mx3, my3 = jpt(cx + rw * 0.32, cy + rh * 0.28, 0.4)
    L.append(f'<path d="M {mx1:.1f},{my1:.1f} Q {mx2:.1f},{my2:.1f} {mx3:.1f},{my3:.1f}" '
             f'fill="none" stroke="#888" stroke-width="0.8"/>')

    # Segno/runa sulla fronte
    fx, fy = cx + rng.uniform(-0.5, 0.5), cy - rh * 0.55
    s = max(2, tile * 0.1)
    L.append(f'<line x1="{fx-s:.1f}" y1="{fy:.1f}" x2="{fx+s:.1f}" y2="{fy:.1f}" '
             f'stroke="#c00" stroke-width="0.8"/>')
    L.append(f'<line x1="{fx:.1f}" y1="{fy-s:.1f}" x2="{fx:.1f}" y2="{fy+s*0.5:.1f}" '
             f'stroke="#c00" stroke-width="0.8"/>')

    # Gancio in cima
    L.append(f'<line x1="{cx:.1f}" y1="{oy:.1f}" x2="{cx:.1f}" y2="{oy+oh*0.08:.1f}" '
             f'stroke="black" stroke-width="1"/>')
