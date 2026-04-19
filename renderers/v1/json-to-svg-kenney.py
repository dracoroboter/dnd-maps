#!/usr/bin/env python3
"""
json-to-svg-kenney.py v0.1 — Renderer SVG stile Kenney Scribble Dungeons.

COMPATIBILITÀ: generate-dungeon.py cell-grid-0.3+
USO: python3 renderers/v1/json-to-svg-kenney.py <input.json> [--tile-size N] [--tileset DIR] [--output FILE]

TILESET: goodExamples/kenney_scribble-dungeons/PNG/Default (64px)/
"""

import argparse
import base64
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from dungeon_svg_core import (
    load_data, rebuild_grid, get_grid_size, get_passages,
    bounding_box, is_exterior_wall, write_svg,
    EXTERIOR, WALL, FLOOR, CORR
)

TILE = 64
TILESET = "goodExamples/kenney_scribble-dungeons/PNG/Default (64px)"


def b64(path):
    try:
        with open(path, 'rb') as f:
            return 'data:image/png;base64,' + base64.b64encode(f.read()).decode()
    except Exception:
        return None


def wall_tile_svg(px, py, tile, grid, x, y, gh, gw, t_wall):
    """wall.png = bordo top+bottom. Angoli: sovrappone orizzontale + verticale."""
    u = grid[y-1][x] if y > 0    else EXTERIOR
    d = grid[y+1][x] if y < gh-1 else EXTERIOR
    l = grid[y][x-1] if x > 0    else EXTERIOR
    r = grid[y][x+1] if x < gw-1 else EXTERIOR
    fl = l in (FLOOR, CORR); fr = r in (FLOOR, CORR)
    fu = u in (FLOOR, CORR); fd = d in (FLOOR, CORR)
    cx, cy = px + tile//2, py + tile//2

    if not t_wall:
        return f'<rect x="{px}" y="{py}" width="{tile}" height="{tile}" fill="#888"/>'

    horiz = f'<image href="{t_wall}" x="{px}" y="{py}" width="{tile}" height="{tile}"/>'
    vert  = f'<image href="{t_wall}" x="{px}" y="{py}" width="{tile}" height="{tile}" transform="rotate(90,{cx},{cy})"/>'

    if (fl or fr) and (fu or fd):
        # Angolo: sovrapponi entrambi
        return horiz + vert
    if (fl or fr) and not fu and not fd:
        return vert
    return horiz


def render(data, tile, tileset_dir, output_path):
    rooms = data['rooms']
    title = data.get('title', 'Dungeon')
    year  = (data.get('generated') or '')[:4] or '2026'
    gw, gh = get_grid_size(data)
    grid  = rebuild_grid(rooms, gw, gh)
    doors = get_passages(data)
    bb    = bounding_box(grid, gw, gh)
    if not bb:
        return
    x0, y0, x1, y1 = bb
    W, H, header_h = (x1-x0)*tile, (y1-y0)*tile, 80

    t_floor = b64(os.path.join(tileset_dir, 'tile.png'))
    t_wall  = b64(os.path.join(tileset_dir, 'wall.png'))
    t_door  = b64(os.path.join(tileset_dir, 'door_open.png'))

    L = []
    L.append('<?xml version="1.0" encoding="UTF-8"?>')
    L.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H+header_h}" viewBox="0 0 {W} {H+header_h}">')
    L.append('<defs>')
    if t_floor:
        L.append(f'<pattern id="p_floor" patternUnits="userSpaceOnUse" width="{tile}" height="{tile}"><image href="{t_floor}" width="{tile}" height="{tile}"/></pattern>')
    L.append('</defs>')

    L.append(f'<rect width="{W}" height="{H+header_h}" fill="white"/>')
    L.append(f'<rect width="{W}" height="{header_h}" fill="#f5f0e8"/>')
    L.append(f'<line x1="0" y1="{header_h}" x2="{W}" y2="{header_h}" stroke="#333" stroke-width="2"/>')
    L.append(f'<text x="{W//2}" y="44" text-anchor="middle" font-family="Georgia,serif" font-size="28" font-weight="bold" fill="#1a1008">{title}</text>')
    L.append(f'<text x="{W//2}" y="66" text-anchor="middle" font-family="sans-serif" font-size="12" fill="#666">© {year} Dracosoft — CC BY</text>')
    L.append(f'<g transform="translate(0,{header_h})">')

    for y in range(y0, y1):
        for x in range(x0, x1):
            px, py = (x-x0)*tile, (y-y0)*tile
            v = grid[y][x]
            if v == EXTERIOR:
                continue
            elif v == WALL:
                if (x, y) in doors:
                    # Porta: pavimento + door_open
                    fill = 'url(#p_floor)' if t_floor else '#f5f0e8'
                    L.append(f'<rect x="{px}" y="{py}" width="{tile}" height="{tile}" fill="{fill}"/>')
                    if t_door:
                        orient = doors[(x, y)]
                        if orient == 'h':
                            # Muro orizzontale: celle affiancate orizzontalmente (stessa y, x diverse)
                            # cella sinistra (x minore) → 2: flipx
                            # cella destra (x maggiore) → 1: normale
                            prev = (x-1, y)
                            is_right = prev in doors and doors[prev] == orient
                            if is_right:
                                L.append(f'<image href="{t_door}" x="{px}" y="{py}" width="{tile}" height="{tile}"/>')
                            else:
                                L.append(f'<g transform="translate({px},{py})"><g transform="scale(-1,1) translate(-{tile},0)"><image href="{t_door}" x="0" y="0" width="{tile}" height="{tile}"/></g></g>')
                        else:
                            # Muro verticale: celle affiancate verticalmente (stessa x, y diverse)
                            # cella in alto (y minore) → 7: rot+90 flipx
                            # cella in basso (y maggiore) → 4: rot+90
                            prev = (x, y-1)
                            is_bottom = prev in doors and doors[prev] == orient
                            if is_bottom:
                                L.append(f'<g transform="translate({px},{py})"><g transform="rotate(90,{tile//2},{tile//2})"><image href="{t_door}" x="0" y="0" width="{tile}" height="{tile}"/></g></g>')
                            else:
                                L.append(f'<g transform="translate({px},{py})"><g transform="rotate(90,{tile//2},{tile//2}) scale(-1,1) translate(-{tile},0)"><image href="{t_door}" x="0" y="0" width="{tile}" height="{tile}"/></g></g>')
                else:
                    L.append(wall_tile_svg(px, py, tile, grid, x, y, gh, gw, t_wall))
            else:
                fill = 'url(#p_floor)' if t_floor else '#f5f0e8'
                L.append(f'<rect x="{px}" y="{py}" width="{tile}" height="{tile}" fill="{fill}"/>')

    # Etichette
    fs = max(14, tile//3)
    for room in rooms:
        rx2, ry2, rw, rh = room['x'], room['y'], room['w'], room['h']
        cx = (rx2+rw/2-x0)*tile
        cy = (ry2+rh/2-y0)*tile
        bw = len(room['id'])*fs*0.7
        L.append(f'<rect x="{cx-bw/2:.0f}" y="{cy-fs:.0f}" width="{bw:.0f}" height="{fs*1.4:.0f}" fill="rgba(255,255,255,0.85)" rx="4"/>')
        L.append(f'<text x="{cx:.1f}" y="{cy+fs*0.35:.1f}" text-anchor="middle" font-family="sans-serif" font-size="{fs}" font-weight="bold" fill="#1a1008">{room["id"]}</text>')

    L.append('</g>')
    L.append('</svg>')
    write_svg(output_path, L)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('input')
    p.add_argument('--tile-size', type=int, default=TILE, dest='tile_size')
    p.add_argument('--tileset',   default=TILESET)
    p.add_argument('--output',    default=None)
    args = p.parse_args()
    data = load_data(args.input)
    output = args.output or os.path.splitext(args.input)[0] + '_kenney.svg'
    render(data, args.tile_size, args.tileset, output)
    print(f'✓ {output}')


if __name__ == '__main__':
    main()
