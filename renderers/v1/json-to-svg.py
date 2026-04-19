#!/usr/bin/env python3
"""
json-to-svg.py v0.2 — Renderer SVG con tileset PNG.

COMPATIBILITÀ: generate-dungeon.py cell-grid-0.3+
USO: python3 renderers/v1/json-to-svg.py <input.json> [--tile-size N] [--tileset DIR] [--output FILE]

TILESET: directory con floor.png, wall.png, floor_stone.png (opzionale).
  Default: assets/tilesets/dcss/
  Alternativi: Kenney Dungeon Tileset (kenney.nl/assets/dungeon-tileset, CC0)
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

TILE = 20


def png_to_b64(path):
    try:
        with open(path, 'rb') as f:
            return 'data:image/png;base64,' + base64.b64encode(f.read()).decode()
    except Exception:
        return None


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
    W, H, header_h = (x1-x0)*tile, (y1-y0)*tile, 56

    floor_b64 = png_to_b64(os.path.join(tileset_dir, 'floor.png'))
    wall_b64  = png_to_b64(os.path.join(tileset_dir, 'wall.png'))
    corr_b64  = png_to_b64(os.path.join(tileset_dir, 'floor_stone.png')) or floor_b64

    L = []
    L.append('<?xml version="1.0" encoding="UTF-8"?>')
    L.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H+header_h}" viewBox="0 0 {W} {H+header_h}">')
    L.append('<defs>')
    if floor_b64:
        L.append(f'<pattern id="p_floor" patternUnits="userSpaceOnUse" width="{tile}" height="{tile}"><image href="{floor_b64}" width="{tile}" height="{tile}"/></pattern>')
    if wall_b64:
        L.append(f'<pattern id="p_wall_int" patternUnits="userSpaceOnUse" width="{tile}" height="{tile}"><image href="{wall_b64}" width="{tile}" height="{tile}"/></pattern>')
        L.append(f'<pattern id="p_wall_ext" patternUnits="userSpaceOnUse" width="{tile}" height="{tile}"><image href="{wall_b64}" width="{tile}" height="{tile}"/><rect width="{tile}" height="{tile}" fill="rgba(0,0,0,0.45)"/></pattern>')
    if corr_b64:
        L.append(f'<pattern id="p_corr" patternUnits="userSpaceOnUse" width="{tile}" height="{tile}"><image href="{corr_b64}" width="{tile}" height="{tile}"/></pattern>')
    L.append(f'<pattern id="hatch_int" patternUnits="userSpaceOnUse" width="6" height="6"><rect width="6" height="6" fill="#787068"/><line x1="0" y1="6" x2="6" y2="0" stroke="#5a5248" stroke-width="1"/></pattern>')
    L.append(f'<pattern id="hatch_ext" patternUnits="userSpaceOnUse" width="6" height="6"><rect width="6" height="6" fill="#1e1e1e"/><line x1="0" y1="6" x2="6" y2="0" stroke="#0a0a0a" stroke-width="1.5"/></pattern>')
    L.append(f'<pattern id="grid_floor" patternUnits="userSpaceOnUse" width="{tile}" height="{tile}"><rect width="{tile}" height="{tile}" fill="#f0e6b4"/><rect width="{tile}" height="{tile}" fill="none" stroke="#c8b87a" stroke-width="0.5"/></pattern>')
    L.append(f'<pattern id="grid_corr" patternUnits="userSpaceOnUse" width="{tile}" height="{tile}"><rect width="{tile}" height="{tile}" fill="#dcb478"/><rect width="{tile}" height="{tile}" fill="none" stroke="#b8904a" stroke-width="0.5"/></pattern>')
    L.append('</defs>')

    L.append(f'<rect width="{W}" height="{H+header_h}" fill="white"/>')
    L.append(f'<rect width="{W}" height="{header_h}" fill="#1a1008"/>')
    L.append(f'<text x="{W//2}" y="32" text-anchor="middle" font-family="Georgia,serif" font-size="24" font-weight="bold" fill="#f0d890" letter-spacing="2">{title}</text>')
    L.append(f'<text x="{W//2}" y="48" text-anchor="middle" font-family="sans-serif" font-size="10" fill="#a09070">© {year} Dracosoft — CC BY</text>')
    L.append(f'<g transform="translate(0,{header_h})">')

    # Ombre muri esterni
    for y in range(y0, y1):
        for x in range(x0, x1):
            if grid[y][x] == WALL and (x,y) not in doors and is_exterior_wall(grid, x, y, gh, gw):
                px, py = (x-x0)*tile, (y-y0)*tile
                L.append(f'<rect x="{px+2}" y="{py+2}" width="{tile}" height="{tile}" fill="rgba(0,0,0,0.2)"/>')

    # Celle
    for y in range(y0, y1):
        for x in range(x0, x1):
            px, py = (x-x0)*tile, (y-y0)*tile
            v = grid[y][x]
            if v == 3: continue  # EXTERIOR
            if v == 0:  # WALL
                if (x, y) in doors: continue
                ext = is_exterior_wall(grid, x, y, gh, gw)
                fill = ('url(#p_wall_ext)' if ext else 'url(#p_wall_int)') if wall_b64 else ('url(#hatch_ext)' if ext else 'url(#hatch_int)')
            elif v == 1:  # FLOOR
                fill = 'url(#p_floor)' if floor_b64 else 'url(#grid_floor)'
            else:  # CORR
                fill = 'url(#p_corr)' if corr_b64 else 'url(#grid_corr)'
            L.append(f'<rect x="{px}" y="{py}" width="{tile}" height="{tile}" fill="{fill}"/>')

    # Porte
    dw, dl = max(2, tile//5), max(6, tile*3//4)
    for (dx, dy), orient in doors.items():
        if not (x0 <= dx < x1 and y0 <= dy < y1): continue
        px, py = (dx-x0)*tile, (dy-y0)*tile
        cx, cy = px+tile//2, py+tile//2
        adj = 'url(#p_floor)' if floor_b64 else 'url(#grid_floor)'
        L.append(f'<rect x="{px}" y="{py}" width="{tile}" height="{tile}" fill="{adj}"/>')
        if orient == 'h':
            L.append(f'<rect x="{cx-dw}" y="{cy-dl//2}" width="{dw*2}" height="{dl}" fill="#3d1f08" stroke="#c8a060" stroke-width="1" rx="1"/>')
        else:
            L.append(f'<rect x="{cx-dl//2}" y="{cy-dw}" width="{dl}" height="{dw*2}" fill="#3d1f08" stroke="#c8a060" stroke-width="1" rx="1"/>')

    # Etichette
    fs = max(8, tile-4)
    for room in rooms:
        rx2, ry2, rw, rh = room['x'], room['y'], room['w'], room['h']
        cx = (rx2+rw/2-x0)*tile
        cy = (ry2+rh/2-y0)*tile
        bf = 'rgba(220,180,120,0.85)' if room['type']=='corridor' else 'rgba(240,230,180,0.85)'
        bw = len(room['id'])*fs*0.7
        L.append(f'<rect x="{cx-bw/2:.1f}" y="{cy-fs*0.75:.1f}" width="{bw:.1f}" height="{fs*1.1:.1f}" fill="{bf}" rx="3" stroke="#8a7040" stroke-width="0.5"/>')
        L.append(f'<text x="{cx:.1f}" y="{cy+fs*0.3:.1f}" text-anchor="middle" font-family="sans-serif" font-size="{fs}" font-weight="bold" fill="#1a1008">{room["id"]}</text>')

    L.append('</g>')
    L.append('</svg>')
    write_svg(output_path, L)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('input')
    p.add_argument('--tile-size', type=int, default=TILE, dest='tile_size')
    p.add_argument('--tileset',   default='assets/tilesets/dcss')
    p.add_argument('--output',    default=None)
    args = p.parse_args()
    data = load_data(args.input)
    output = args.output or os.path.splitext(args.input)[0] + '.svg'
    render(data, args.tile_size, args.tileset, output)
    print(f'✓ {output}')


if __name__ == '__main__':
    main()
