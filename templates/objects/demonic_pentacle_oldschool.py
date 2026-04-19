"""Plugin OLDSCHOOL: demonic_pentacle (pentacolo demoniaco 5×5) — stile mano libera."""
import random, math


def _jpt(x, y, rng, amp=1.0):
    return x + rng.uniform(-amp, amp), y + rng.uniform(-amp, amp)


def _jline(x1, y1, x2, y2, rng, amp=1.0, segs=4):
    pts = [(x1, y1)]
    for i in range(1, segs):
        t = i / segs
        pts.append((x1+(x2-x1)*t + rng.uniform(-amp, amp),
                    y1+(y2-y1)*t + rng.uniform(-amp, amp)))
    pts.append((x2, y2))
    return 'M ' + ' L '.join(f'{p[0]:.1f},{p[1]:.1f}' for p in pts)


def render(obj, tpl, ox, oy, ow, oh, tile, L):
    rng = random.Random(hash((ox, oy)))
    cx, cy = ox + ow / 2, oy + oh / 2
    r_outer = min(ow, oh) / 2 * 0.85   # cerchio esterno
    r_inner = r_outer * 0.38            # cerchio interno (pentagono)
    r_rune  = r_outer * 1.08            # raggio simboli runici

    # Cerchio esterno jitterizzato
    pts = []
    for a in range(0, 360, 8):
        rad = math.radians(a)
        jr = r_outer + rng.uniform(-1.2, 1.2)
        pts.append(f'{cx+jr*math.cos(rad):.1f},{cy+jr*math.sin(rad):.1f}')
    L.append(f'<polygon points="{" ".join(pts)}" fill="none" stroke="black" stroke-width="1.2"/>')

    # Stella a 5 punte (pentagramma) — disegnata come 5 linee che si incrociano
    # Vertici della stella: angoli a -90°, poi ogni 72°
    star_pts = []
    for i in range(5):
        a = math.radians(-90 + i * 72)
        star_pts.append((cx + r_outer * 0.82 * math.cos(a),
                         cy + r_outer * 0.82 * math.sin(a)))

    # Disegna le 5 corde del pentagramma (ogni vertice collegato al 2° successivo)
    for i in range(5):
        x1, y1 = star_pts[i]
        x2, y2 = star_pts[(i + 2) % 5]
        L.append(f'<path d="{_jline(x1,y1,x2,y2,rng,amp=1.0,segs=3)}" stroke="black" stroke-width="1" fill="none"/>')

    # Cerchio interno
    pts2 = []
    for a in range(0, 360, 12):
        rad = math.radians(a)
        jr = r_inner + rng.uniform(-0.8, 0.8)
        pts2.append(f'{cx+jr*math.cos(rad):.1f},{cy+jr*math.sin(rad):.1f}')
    L.append(f'<polygon points="{" ".join(pts2)}" fill="none" stroke="black" stroke-width="0.8"/>')

    # Simboli runici: piccole croci/segni tra i vertici della stella
    for i in range(5):
        a = math.radians(-90 + i * 72 + 36)  # tra i vertici
        rx = cx + r_rune * math.cos(a)
        ry = cy + r_rune * math.sin(a)
        s = max(2, tile // 8)
        jx, jy = rng.uniform(-0.5, 0.5), rng.uniform(-0.5, 0.5)
        # Piccola croce runica
        L.append(f'<line x1="{rx-s+jx:.1f}" y1="{ry+jy:.1f}" x2="{rx+s+jx:.1f}" y2="{ry+jy:.1f}" stroke="black" stroke-width="0.8"/>')
        L.append(f'<line x1="{rx+jx:.1f}" y1="{ry-s+jy:.1f}" x2="{rx+jx:.1f}" y2="{ry+s*0.4+jy:.1f}" stroke="black" stroke-width="0.8"/>')
