#!/usr/bin/env python3
"""
json2-to-svg.py — Renderer SVG oldschool per formato dungeon JSON v2
Uso: python3 json2-to-svg.py <file.json> [-o output.svg] [--view dm|players] [--seed N]
"""

import json, sys, os, math, random

SQ = 30
MARGIN = 40
WALL_SW = 2.0
FONT = "Georgia, serif"
HATCH_RADIUS = 4  # quadretti di hatching intorno alle stanze


def hatch_cell(cx, cy, size, rng, density=14):
    """Tassellatura a parquet: linee incrociate irregolari."""
    lines = []
    step = size / 2.5  # tasselli più grandi
    jitter = size * 0.08  # irregolarità
    # Linee a +45°
    for i in range(-3, 6):
        x_start = cx + i * step + rng.uniform(-jitter, jitter)
        x_end = x_start + size
        lx1 = max(cx, min(cx + size, x_start))
        ly1 = cy + (lx1 - x_start)
        lx2 = max(cx, min(cx + size, x_end))
        ly2 = cy + size - (x_end - lx2)
        ly1 = max(cy, min(cy + size, ly1))
        ly2 = max(cy, min(cy + size, ly2))
        if abs(lx2 - lx1) > 1 or abs(ly2 - ly1) > 1:
            lines.append(f'<line x1="{lx1:.1f}" y1="{ly1:.1f}" x2="{lx2:.1f}" y2="{ly2:.1f}" '
                         f'stroke="black" stroke-width="0.4" opacity="{0.35 + rng.uniform(0, 0.2):.2f}"/>')
    # Linee a -45°
    for i in range(-3, 6):
        x_start = cx + i * step + rng.uniform(-jitter, jitter)
        x_end = x_start + size
        lx1 = max(cx, min(cx + size, x_start))
        ly1 = cy + size - (lx1 - x_start)
        lx2 = max(cx, min(cx + size, x_end))
        ly2 = cy + (x_end - lx2)
        ly1 = max(cy, min(cy + size, ly1))
        ly2 = max(cy, min(cy + size, ly2))
        if abs(lx2 - lx1) > 1 or abs(ly2 - ly1) > 1:
            lines.append(f'<line x1="{lx1:.1f}" y1="{ly1:.1f}" x2="{lx2:.1f}" y2="{ly2:.1f}" '
                         f'stroke="black" stroke-width="0.4" opacity="{0.35 + rng.uniform(0, 0.2):.2f}"/>')
    return "\n".join(lines)


def s(v): return v * SQ

def area_bounds(a):
    sh = a["shape"]
    if sh == "rect": return (a["x"], a["y"], a["x"]+a["w"], a["y"]+a["h"])
    elif sh == "circle": return (a["cx"]-a["r"], a["cy"]-a["r"], a["cx"]+a["r"], a["cy"]+a["r"])
    elif sh == "poly":
        xs, ys = zip(*a["points"])
        return (min(xs), min(ys), max(xs), max(ys))
    return (0,0,0,0)

def area_center(a):
    sh = a["shape"]
    if sh == "rect": return (a["x"]+a["w"]/2, a["y"]+a["h"]/2)
    elif sh == "circle": return (a["cx"], a["cy"])
    elif sh == "poly":
        xs, ys = zip(*a["points"])
        return (sum(xs)/len(xs), sum(ys)/len(ys))
    return (0,0)

def edge_point(a, target):
    cx, cy = area_center(a)
    tx, ty = target
    dx, dy = tx-cx, ty-cy
    if a["shape"] == "rect":
        x1,y1,x2,y2 = a["x"],a["y"],a["x"]+a["w"],a["y"]+a["h"]
        if abs(dx)<0.01 and abs(dy)<0.01: return (cx, y2)
        cands = []
        if dx != 0:
            for bx in [x1,x2]:
                t = (bx-cx)/dx
                if t > 0:
                    py = cy+t*dy
                    if y1-0.1<=py<=y2+0.1: cands.append((bx,py,t))
        if dy != 0:
            for by in [y1,y2]:
                t = (by-cy)/dy
                if t > 0:
                    px = cx+t*dx
                    if x1-0.1<=px<=x2+0.1: cands.append((px,by,t))
        if cands: b=min(cands,key=lambda c:c[2]); return (b[0],b[1])
        return (cx,cy)
    elif a["shape"] == "circle":
        dist = math.sqrt(dx*dx+dy*dy)
        if dist<0.01: return (cx, cy+a["r"])
        return (cx+dx/dist*a["r"], cy+dy/dist*a["r"])
    return (cx,cy)


def cells_near_areas(areas, radius):
    """Restituisce set di (gx,gy) celle entro radius quadretti da qualsiasi area."""
    cells = set()
    for a in areas:
        b = area_bounds(a)
        x0, y0 = int(math.floor(b[0])) - radius, int(math.floor(b[1])) - radius
        x1, y1 = int(math.ceil(b[2])) + radius, int(math.ceil(b[3])) + radius
        for gx in range(x0, x1):
            for gy in range(y0, y1):
                cells.add((gx, gy))
    return cells


def point_in_area(px, py, a):
    """Controlla se un punto (in unità quadretti) è dentro un'area."""
    sh = a["shape"]
    if sh == "rect":
        return a["x"] <= px <= a["x"]+a["w"] and a["y"] <= py <= a["y"]+a["h"]
    elif sh == "circle":
        dx, dy = px - a["cx"], py - a["cy"]
        return dx*dx + dy*dy <= a["r"]*a["r"]
    return False


def svg_area_white(a):
    sh = a["shape"]
    if sh == "rect":
        return f'<rect x="{s(a["x"])}" y="{s(a["y"])}" width="{s(a["w"])}" height="{s(a["h"])}" fill="white" stroke="none"/>\n'
    elif sh == "circle":
        return f'<circle cx="{s(a["cx"])}" cy="{s(a["cy"])}" r="{s(a["r"])}" fill="white" stroke="none"/>\n'
    elif sh == "poly":
        pts = " ".join(f"{s(p[0])},{s(p[1])}" for p in a["points"])
        return f'<polygon points="{pts}" fill="white" stroke="none"/>\n'
    return ""

def svg_area_border(a):
    sh = a["shape"]
    if sh == "rect":
        return f'<rect x="{s(a["x"])}" y="{s(a["y"])}" width="{s(a["w"])}" height="{s(a["h"])}" fill="none" stroke="black" stroke-width="{WALL_SW}"/>\n'
    elif sh == "circle":
        return f'<circle cx="{s(a["cx"])}" cy="{s(a["cy"])}" r="{s(a["r"])}" fill="none" stroke="black" stroke-width="{WALL_SW}"/>\n'
    elif sh == "poly":
        pts = " ".join(f"{s(p[0])},{s(p[1])}" for p in a["points"])
        return f'<polygon points="{pts}" fill="none" stroke="black" stroke-width="{WALL_SW}"/>\n'
    return ""

def svg_area_grid(a):
    svg = ""
    b = area_bounds(a)
    x0,y0 = int(math.floor(b[0])), int(math.floor(b[1]))
    x1,y1 = int(math.ceil(b[2])), int(math.ceil(b[3]))
    for gx in range(x0, x1+1):
        svg += f'<line x1="{s(gx)}" y1="{s(y0)}" x2="{s(gx)}" y2="{s(y1)}" stroke="#ccc" stroke-width="0.4"/>\n'
    for gy in range(y0, y1+1):
        svg += f'<line x1="{s(x0)}" y1="{s(gy)}" x2="{s(x1)}" y2="{s(gy)}" stroke="#ccc" stroke-width="0.4"/>\n'
    return svg


def _conn_endpoints(conn, ad):
    """Calcola p1, p2 (in unità quadretti) per una connessione."""
    a_from = ad.get(conn.get("from"))
    a_to = ad.get(conn.get("to"))
    if not a_from:
        return None, None
    if a_to:
        c1, c2 = area_center(a_from), area_center(a_to)
        return edge_point(a_from, c2), edge_point(a_to, c1)
    else:
        bx1, by1, bx2, by2 = area_bounds(a_from)
        cx, cy = area_center(a_from)
        side = conn.get("side", "south")
        if side == "south":   return (cx, by2), (cx, by2 + 1.5)
        elif side == "north": return (cx, by1), (cx, by1 - 1.5)
        elif side == "east":  return (bx2, cy), (bx2 + 1.5, cy)
        else:                 return (bx1, cy), (bx1 - 1.5, cy)


def _perp(dx, dy):
    """Vettore perpendicolare unitario (ruotato 90° antiorario)."""
    length = math.sqrt(dx * dx + dy * dy)
    if length < 0.001:
        return (0, 1)
    return (-dy / length, dx / length)


def svg_connection(conn, ad):
    a_from = ad.get(conn.get("from"))
    if not a_from:
        return ""
    ctype = conn.get("type", "tunnel")
    width = conn.get("width", 1)

    p1, p2 = _conn_endpoints(conn, ad)
    if p1 is None:
        return ""

    # Direzione del corridoio (in quadretti)
    ddx, ddy = p2[0] - p1[0], p2[1] - p1[1]
    length = math.sqrt(ddx * ddx + ddy * ddy)
    if length < 0.01:
        return ""

    # Vettore unitario lungo il corridoio e perpendicolare
    ux, uy = ddx / length, ddy / length
    nx, ny = _perp(ddx, ddy)

    # Estensione dentro i muri delle stanze (in quadretti)
    ext = 0.3
    # Punti estesi
    e1x, e1y = p1[0] - ux * ext, p1[1] - uy * ext
    e2x, e2y = p2[0] + ux * ext, p2[1] + uy * ext

    half_w = width / 2.0

    svg = ""

    if ctype in ("tunnel", "arch"):
        # 4 vertici del corridoio (parallelogramma)
        ax, ay = s(e1x + nx * half_w), s(e1y + ny * half_w)
        bx, by = s(e2x + nx * half_w), s(e2y + ny * half_w)
        cx, cy = s(e2x - nx * half_w), s(e2y - ny * half_w)
        ddx2, ddy2 = s(e1x - nx * half_w), s(e1y - ny * half_w)

        # Sfondo bianco
        pts = f"{ax},{ay} {bx},{by} {cx},{cy} {ddx2},{ddy2}"
        svg += f'<polygon points="{pts}" fill="white" stroke="none"/>\n'

        # Wall-break: linee bianche spesse che cancellano il muro della stanza nel punto di contatto
        wb_sw = WALL_SW + 2  # più spesso del muro
        for px, py in [p1, p2]:
            w1x, w1y = s(px + nx * half_w), s(py + ny * half_w)
            w2x, w2y = s(px - nx * half_w), s(py - ny * half_w)
            svg += f'<line x1="{w1x}" y1="{w1y}" x2="{w2x}" y2="{w2y}" stroke="white" stroke-width="{wb_sw}"/>\n'

        # Bordo sinistro
        svg += f'<line x1="{ax}" y1="{ay}" x2="{bx}" y2="{by}" stroke="black" stroke-width="{WALL_SW}"/>\n'
        # Bordo destro
        svg += f'<line x1="{ddx2}" y1="{ddy2}" x2="{cx}" y2="{cy}" stroke="black" stroke-width="{WALL_SW}"/>\n'

        # Griglia trasversale dentro il corridoio
        steps = int(math.ceil(length))
        for i in range(1, steps):
            t = i / length
            gx = s(p1[0] + (p2[0] - p1[0]) * t)
            gy = s(p1[1] + (p2[1] - p1[1]) * t)
            g1x, g1y = gx + s(nx * half_w), gy + s(ny * half_w)
            g2x, g2y = gx - s(nx * half_w), gy - s(ny * half_w)
            svg += f'<line x1="{g1x:.1f}" y1="{g1y:.1f}" x2="{g2x:.1f}" y2="{g2y:.1f}" stroke="#ccc" stroke-width="0.4"/>\n'

    elif ctype == "door":
        gap_w = 0.8  # larghezza varco porta (in quadretti)
        half_g = gap_w / 2.0

        ax, ay = s(e1x + nx * half_g), s(e1y + ny * half_g)
        bx, by = s(e2x + nx * half_g), s(e2y + ny * half_g)
        cx, cy = s(e2x - nx * half_g), s(e2y - ny * half_g)
        ddx2, ddy2 = s(e1x - nx * half_g), s(e1y - ny * half_g)

        pts = f"{ax},{ay} {bx},{by} {cx},{cy} {ddx2},{ddy2}"
        svg += f'<polygon points="{pts}" fill="white" stroke="none"/>\n'

        # Wall-break
        wb_sw = WALL_SW + 2
        for px, py in [p1, p2]:
            w1x, w1y = s(px + nx * half_g), s(py + ny * half_g)
            w2x, w2y = s(px - nx * half_g), s(py - ny * half_g)
            svg += f'<line x1="{w1x}" y1="{w1y}" x2="{w2x}" y2="{w2y}" stroke="white" stroke-width="{wb_sw}"/>\n'

        svg += f'<line x1="{ax}" y1="{ay}" x2="{bx}" y2="{by}" stroke="black" stroke-width="{WALL_SW}"/>\n'
        svg += f'<line x1="{ddx2}" y1="{ddy2}" x2="{cx}" y2="{cy}" stroke="black" stroke-width="{WALL_SW}"/>\n'

        # Linea trasversale della porta (a metà del passaggio)
        mid_x, mid_y = (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2
        d1x, d1y = s(mid_x + nx * half_g), s(mid_y + ny * half_g)
        d2x, d2y = s(mid_x - nx * half_g), s(mid_y - ny * half_g)
        svg += f'<line x1="{d1x}" y1="{d1y}" x2="{d2x}" y2="{d2y}" stroke="black" stroke-width="{WALL_SW * 0.8}"/>\n'

        # Arco porta (dal lato from)
        mx_px, my_px = s((p1[0] + p2[0]) / 2), s((p1[1] + p2[1]) / 2)
        arc_r = s(gap_w * 0.4)
        svg += f'<circle cx="{s(p1[0])}" cy="{s(p1[1])}" r="{arc_r}" fill="none" stroke="black" stroke-width="1.2" stroke-dasharray="2,2"/>\n'

    elif ctype == "secret":
        mx_px = s((p1[0] + p2[0]) / 2)
        my_px = s((p1[1] + p2[1]) / 2)
        svg += f'<line x1="{s(p1[0])}" y1="{s(p1[1])}" x2="{s(p2[0])}" y2="{s(p2[1])}" stroke="#c00" stroke-width="1" stroke-dasharray="3,3"/>\n'
        svg += f'<text x="{mx_px}" y="{my_px - 5}" text-anchor="middle" font-size="7" fill="#c00" font-family="{FONT}">S</text>\n'

    return svg


def svg_object(obj, ad, view):
    area = ad.get(obj.get("area"))
    if not area: return ""
    if view == "players" and obj.get("hidden"): return ""
    pos = obj.get("pos")
    if pos == "center": ox,oy = area_center(area)
    elif isinstance(pos, list): ox,oy = pos
    else: ox,oy = area_center(area)
    px,py = s(ox),s(oy)
    r = SQ * 0.12
    otype = obj.get("type","")

    if otype == "pillar":
        return f'<circle cx="{px}" cy="{py}" r="{r*2}" fill="#ccc" stroke="black" stroke-width="1.2"/>\n'
    elif otype == "trap":
        return (f'<line x1="{px-r*2.5}" y1="{py-r*2.5}" x2="{px+r*2.5}" y2="{py+r*2.5}" stroke="#c00" stroke-width="1.5"/>\n'
                f'<line x1="{px+r*2.5}" y1="{py-r*2.5}" x2="{px-r*2.5}" y2="{py+r*2.5}" stroke="#c00" stroke-width="1.5"/>\n')
    elif otype == "grate":
        gs = r*3
        return (f'<rect x="{px-gs}" y="{py-gs}" width="{gs*2}" height="{gs*2}" fill="none" stroke="black" stroke-width="1"/>\n'
                f'<line x1="{px}" y1="{py-gs}" x2="{px}" y2="{py+gs}" stroke="black" stroke-width="0.5"/>\n'
                f'<line x1="{px-gs}" y1="{py}" x2="{px+gs}" y2="{py}" stroke="black" stroke-width="0.5"/>\n')
    elif otype in ("table","counter"):
        return f'<rect x="{px-r*3}" y="{py-r*2}" width="{r*6}" height="{r*4}" fill="none" stroke="black" stroke-width="0.8"/>\n'
    elif otype == "fireplace":
        fw = r*4
        return (f'<rect x="{px-fw}" y="{py-r}" width="{fw*2}" height="{r*2}" fill="none" stroke="black" stroke-width="1.5"/>\n'
                f'<line x1="{px-fw*0.6}" y1="{py}" x2="{px+fw*0.6}" y2="{py}" stroke="black" stroke-width="0.5"/>\n')
    elif otype == "barrel":
        return f'<circle cx="{px}" cy="{py}" r="{r*2}" fill="none" stroke="black" stroke-width="0.8"/>\n'
    return ""


def render(data, view="dm", seed=42):
    rng = random.Random(seed)
    areas = data.get("areas", [])
    conns = data.get("connections", [])
    objs = data.get("objects", [])
    meta = data.get("meta", {})
    ad = {a["id"]: a for a in areas}

    vis = [a for a in areas if not (view=="players" and "secret" in a.get("tags",[]))]
    bounds = [area_bounds(a) for a in vis]
    mn_x = min(b[0] for b in bounds) - 2
    mn_y = min(b[1] for b in bounds) - 2
    mx_x = max(b[2] for b in bounds) + 2
    mx_y = max(b[3] for b in bounds) + 2

    header_h = 50
    footer_h = 25
    w = s(mx_x-mn_x) + MARGIN*2
    h = s(mx_y-mn_y) + MARGIN*2 + header_h + footer_h
    vx = s(mn_x) - MARGIN
    vy = s(mn_y) - MARGIN
    cx_page = vx + w/2

    L = []
    L.append(f'<?xml version="1.0" encoding="UTF-8"?>')
    L.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="{vx} {vy-header_h} {w} {h}">')
    L.append(f'<rect x="{vx}" y="{vy-header_h}" width="{w}" height="{h}" fill="white"/>')

    # Header centrato
    name = meta.get("name", "")
    view_label = "[DM]" if view == "dm" else "[Players]"
    L.append(f'<text x="{cx_page}" y="{vy-header_h+28}" text-anchor="middle" font-family="{FONT}" font-size="22" font-weight="bold" fill="black">{name}  {view_label}</text>')
    # Riga sotto il titolo
    L.append(f'<line x1="{vx+20}" y1="{vy-header_h+35}" x2="{vx+w-20}" y2="{vy-header_h+35}" stroke="#ccc" stroke-width="0.5"/>')

    # Hatching solo intorno alle stanze (HATCH_RADIUS quadretti)
    hatch_cells = cells_near_areas(vis, HATCH_RADIUS)
    L.append('<g>')
    for (gx, gy) in hatch_cells:
        # Non tratteggiare dentro le stanze
        cell_cx, cell_cy = gx + 0.5, gy + 0.5
        inside = any(point_in_area(cell_cx, cell_cy, a) for a in vis)
        if not inside:
            L.append(hatch_cell(s(gx), s(gy), SQ, rng, density=14))
    L.append('</g>')

    # Aree bianche
    for a in vis:
        L.append(svg_area_white(a))

    # Griglia dentro le aree
    L.append('<g>')
    for a in vis: L.append(svg_area_grid(a))
    L.append('</g>')

    # Bordi aree
    for a in vis: L.append(svg_area_border(a))

    # Connessioni (corridoi) — dopo i bordi, così il wall-break li interrompe
    for c in conns:
        if view=="players" and c.get("type")=="secret": continue
        L.append(svg_connection(c, ad))

    # Oggetti
    for o in objs: L.append(svg_object(o, ad, view))

    # Label
    for a in vis:
        cx, cy = area_center(a)
        L.append(f'<text x="{s(cx)}" y="{s(cy)+4}" text-anchor="middle" font-family="{FONT}" font-size="11" font-weight="bold" fill="#333">{a["id"]}</text>')

    # Footer (destra in basso)
    author = meta.get("author", "")
    date = meta.get("date", "")
    lic = meta.get("license", "")
    footer = f"© {author} — {date} — {lic}" if author else ""
    fy = vy - header_h + h - 8
    L.append(f'<rect x="{vx}" y="{fy-14}" width="{w}" height="{22}" fill="white"/>')
    L.append(f'<line x1="{vx+20}" y1="{fy-14}" x2="{vx+w-20}" y2="{fy-14}" stroke="#ccc" stroke-width="0.5"/>')
    L.append(f'<text x="{vx+w-25}" y="{fy}" text-anchor="end" font-family="sans-serif" font-size="8" fill="#999">{footer}</text>')

    L.append('</svg>')
    return "\n".join(L)


def main():
    args = sys.argv[1:]
    if not args:
        print("Uso: python3 json2-to-svg.py <file.json> [-o output.svg] [--view dm|players] [--seed N]")
        sys.exit(1)
    inp = args[0]
    out, view, seed = None, "dm", 42
    if "-o" in args: out = args[args.index("-o")+1]
    if "--view" in args: view = args[args.index("--view")+1]
    if "--seed" in args: seed = int(args[args.index("--seed")+1])
    if not out: out = os.path.splitext(inp)[0] + ".svg"

    with open(inp) as f: data = json.load(f)
    with open(out, "w") as f: f.write(render(data, view, seed))
    print(f"✓ {inp} → {out} (view: {view}, seed: {seed})")

if __name__ == "__main__":
    main()
