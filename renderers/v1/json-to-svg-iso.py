#!/usr/bin/env python3
"""
json-to-svg-iso.py — Renderer isometrico prototipo (B&W, proiezione 2:1).

Proiezione: x_iso = (x - y) * tw/2
            y_iso = (x + y) * th/2  (th = tw/2)
Muri: altezza = WALL_H tile
Luce: faccia nord (y-) più chiara, faccia ovest (x-) più scura
"""
import argparse, json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dungeon_svg_core import load_data, rebuild_grid, get_grid_size, get_passages, bounding_box, WALL, FLOOR, CORR, EXTERIOR

TILE   = 24
WALL_H = 2   # altezza muro in tile

def iso(x, y, tw, th):
    """Coordinate griglia → pixel isometrici."""
    return (x - y) * tw // 2, (x + y) * th // 2

def render(data, tile, output_path):
    rooms = data['rooms']
    gw, gh = get_grid_size(data)
    passages = get_passages(data)
    grid = rebuild_grid(rooms, gw, gh)
    bb = bounding_box(grid, gw, gh, margin=2)
    if not bb: return
    x0, y0, x1, y1 = bb

    tw = tile        # larghezza tile isometrico
    th = tile // 2   # altezza tile isometrico (proiezione 2:1)
    wh = WALL_H * th # altezza muro in pixel

    # Calcola bounds SVG
    # Leftmost corner: (x0, y1), rightmost: (x1, y0)
    # Topmost: (x0, y0), bottommost: (x1, y1)
    corners = [(x0,y0),(x1,y0),(x0,y1),(x1,y1)]
    iso_pts = [iso(x,y,tw,th) for x,y in corners]
    min_ix = min(p[0] for p in iso_pts) - tw
    max_ix = max(p[0] for p in iso_pts) + tw
    min_iy = min(p[1] for p in iso_pts) - wh - th
    max_iy = max(p[1] for p in iso_pts) + th

    W = max_ix - min_ix
    H = max_iy - min_iy
    ox_off = -min_ix
    oy_off = -min_iy

    def p(x, y, dz=0):
        ix, iy = iso(x, y, tw, th)
        return ix + ox_off, iy + oy_off - dz

    def poly(pts, fill, stroke='black', sw=0.8, opacity=1.0):
        s = ' '.join(f'{x:.1f},{y:.1f}' for x,y in pts)
        op = f' opacity="{opacity}"' if opacity < 1 else ''
        return f'<polygon points="{s}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{op}/>'

    L = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}">',
        f'<rect width="{W}" height="{H}" fill="white"/>',
    ]

    # Ordine di rendering: back-to-front (painter's algorithm)
    # Iterate x+y ascending (farthest cells first — painter's algorithm)
    cells = sorted(
        [(x, y) for y in range(y0, y1) for x in range(x0, x1)],
        key=lambda c: c[0] + c[1]
    )

    for (x, y) in cells:
        cell = grid[y][x]
        if cell == EXTERIOR:
            continue

        # Pavimento (top face)
        top = [p(x,y,0), p(x+1,y,0), p(x+1,y+1,0), p(x,y+1,0)]
        if cell == WALL:
            fill_top = '#555'
        elif cell == FLOOR:
            fill_top = 'white'
        else:  # CORR
            fill_top = '#f0f0f0'
        L.append(poly(top, fill_top, sw=0.5))

        # Griglia pavimento
        if cell in (FLOOR, CORR):
            L.append(poly(top, 'none', stroke='#ccc', sw=0.3))

        if cell == WALL and (x, y) not in passages:
            # North face (y- side): lighter
            if y > 0 and grid[y-1][x] != WALL:
                north = [p(x,y,0), p(x+1,y,0), p(x+1,y,wh), p(x,y,wh)]
                L.append(poly(north, '#ddd', sw=0.8))
            # West face (x- side): darker
            if x > 0 and grid[y][x-1] != WALL:
                west = [p(x,y,0), p(x,y+1,0), p(x,y+1,wh), p(x,y,wh)]
                L.append(poly(west, '#aaa', sw=0.8))
            # Top del muro
            top_wall = [p(x,y,wh), p(x+1,y,wh), p(x+1,y+1,wh), p(x,y+1,wh)]
            L.append(poly(top_wall, '#888', sw=0.5))

        elif (x, y) in passages:
            # Porta: pavimento + linea verticale al centro del varco
            orient = passages[(x, y)]
            ph = wh * 0.7  # altezza anta
            if orient == 'h':
                # Anta orizzontale: linea da (x,y+0.5) a (x+1,y+0.5) alzata
                mid = [p(x, y+0.5, 0), p(x+1, y+0.5, 0),
                       p(x+1, y+0.5, ph), p(x, y+0.5, ph)]
                L.append(poly(mid, '#ccc', stroke='black', sw=0.8))
            else:
                mid = [p(x+0.5, y, 0), p(x+0.5, y+1, 0),
                       p(x+0.5, y+1, ph), p(x+0.5, y, ph)]
                L.append(poly(mid, '#ccc', stroke='black', sw=0.8))

    # Oggetti: flat sul pavimento (rettangolo isometrico + etichetta)
    enr = data.get('_enrichment', {})
    rooms_map = {r['id']: r for r in rooms}
    for obj in enr.get('objects', []):
        room = rooms_map.get(obj['room'])
        if not room: continue
        import json as _j, importlib.util as _ilu
        tpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'templates', 'objects')
        tpl_path = os.path.join(tpl_dir, f'{obj["type"]}.json')
        tpl = _j.load(open(tpl_path)) if os.path.exists(tpl_path) else {'size':[1,1]}
        sw_obj, sh_obj = tpl['size']
        gx = room['x'] + obj.get('x', 0)
        gy = room['y'] + obj.get('y', 0)
        # Rombo isometrico flat
        top_obj = [p(gx,gy,1), p(gx+sw_obj,gy,1),
                   p(gx+sw_obj,gy+sh_obj,1), p(gx,gy+sh_obj,1)]
        L.append(poly(top_obj, '#e0e0e0', stroke='black', sw=1.0))
        # Etichetta tipo
        lx, ly = p(gx + sw_obj/2, gy + sh_obj/2, 2)
        label = obj['type'][:3]
        L.append(f'<text x="{lx:.0f}" y="{ly:.0f}" text-anchor="middle" font-family="sans-serif" font-size="6" fill="#333">{label}</text>')

    L.append('</svg>')
    with open(output_path, 'w') as f:
        f.write('\n'.join(L))
    print(f'✓ {output_path}')

def main():
    p = argparse.ArgumentParser()
    p.add_argument('input')
    p.add_argument('--tile-size', type=int, default=TILE, dest='tile_size')
    p.add_argument('--enrichment', default=None)
    p.add_argument('--output', default=None)
    args = p.parse_args()
    data = load_data(args.input)
    if args.enrichment:
        data['_enrichment'] = json.load(open(args.enrichment))
    output = args.output or os.path.splitext(args.input)[0] + '_iso.svg'
    render(data, args.tile_size, output)

if __name__ == '__main__':
    main()
