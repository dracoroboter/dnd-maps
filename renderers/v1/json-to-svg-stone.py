#!/usr/bin/env python3
"""
json-to-svg-stone.py v0.1 — Renderer SVG con texture pietra procedurale (Pillow).

COMPATIBILITÀ: generate-dungeon.py cell-grid-0.3+
USO: python3 renderers/v1/json-to-svg-stone.py <input.json> [--tile-size N] [--seed N] [--output FILE]

Nessun asset esterno richiesto. Texture generate proceduralmente con Pillow.
"""

import argparse
import base64
import io
import os
import random
import sys
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(__file__))
from dungeon_svg_core import (
    load_data, rebuild_grid, get_grid_size, get_passages,
    bounding_box, is_exterior_wall, write_svg,
    EXTERIOR, WALL, FLOOR, CORR
)

TILE = 32


def make_floor_tile(size, rng):
    img = Image.new('RGB', (size, size), (210, 200, 185))
    draw = ImageDraw.Draw(img)
    for _ in range(12):
        x1, y1 = rng.randint(0, size), rng.randint(0, size)
        x2 = x1 + rng.randint(-size//2, size//2)
        y2 = y1 + rng.randint(-size//2, size//2)
        c = rng.randint(170, 195)
        draw.line([(x1,y1),(x2,y2)], fill=(c, c-5, c-10), width=1)
    draw.rectangle([0, 0, size-1, size-1], outline=(180, 170, 155), width=1)
    return img.filter(ImageFilter.GaussianBlur(0.5))


def make_wall_tile(size, rng, dark=False):
    base = (80, 75, 68) if dark else (110, 105, 95)
    img = Image.new('RGB', (size, size), base)
    draw = ImageDraw.Draw(img)
    bh = size // 3
    for row in range(3):
        offset = (size // 4) if row % 2 else 0
        y = row * bh
        bw = size // 2
        for col in range(-1, 3):
            x = col * bw + offset
            c = rng.randint(-12, 12)
            bc = tuple(max(0, min(255, base[i]+c)) for i in range(3))
            draw.rectangle([x+1, y+1, x+bw-1, y+bh-1], fill=bc)
            draw.rectangle([x, y, x+bw, y+bh], outline=(50, 48, 44), width=1)
    return img.filter(ImageFilter.GaussianBlur(0.3))


def make_corr_tile(size, rng):
    img = Image.new('RGB', (size, size), (175, 165, 148))
    draw = ImageDraw.Draw(img)
    for _ in range(8):
        x1, y1 = rng.randint(0, size), rng.randint(0, size)
        x2 = x1 + rng.randint(-size//3, size//3)
        y2 = y1 + rng.randint(-size//3, size//3)
        c = rng.randint(145, 165)
        draw.line([(x1,y1),(x2,y2)], fill=(c, c-5, c-8), width=1)
    draw.rectangle([0, 0, size-1, size-1], outline=(150, 140, 125), width=1)
    return img.filter(ImageFilter.GaussianBlur(0.4))


def to_b64(img):
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode()


def render(data, tile, output_path, seed):
    rooms = data['rooms']
    title = data.get('title', 'Dungeon')
    year  = (data.get('generated') or '')[:4] or '2026'
    gw, gh = get_grid_size(data)
    rng   = random.Random(seed)
    grid  = rebuild_grid(rooms, gw, gh)
    doors = get_passages(data)
    bb    = bounding_box(grid, gw, gh)
    if not bb:
        return
    x0, y0, x1, y1 = bb
    W, H, header_h = (x1-x0)*tile, (y1-y0)*tile, 60

    t_floor = to_b64(make_floor_tile(tile, rng))
    t_wall  = to_b64(make_wall_tile(tile, rng, dark=False))
    t_wext  = to_b64(make_wall_tile(tile, rng, dark=True))
    t_corr  = to_b64(make_corr_tile(tile, rng))

    L = []
    L.append('<?xml version="1.0" encoding="UTF-8"?>')
    L.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H+header_h}" viewBox="0 0 {W} {H+header_h}">')
    L.append('<defs>')
    for pid, td in [('p_floor',t_floor),('p_wall',t_wall),('p_wext',t_wext),('p_corr',t_corr)]:
        L.append(f'<pattern id="{pid}" patternUnits="userSpaceOnUse" width="{tile}" height="{tile}"><image href="{td}" width="{tile}" height="{tile}"/></pattern>')
    L.append('</defs>')

    L.append(f'<rect width="{W}" height="{H+header_h}" fill="#111"/>')
    L.append(f'<rect width="{W}" height="{header_h}" fill="#1a1008"/>')
    L.append(f'<text x="{W//2}" y="34" text-anchor="middle" font-family="Georgia,serif" font-size="22" font-weight="bold" fill="#d4b870" letter-spacing="2">{title}</text>')
    L.append(f'<text x="{W//2}" y="52" text-anchor="middle" font-family="sans-serif" font-size="10" fill="#806040">© {year} Dracosoft — CC BY</text>')
    L.append(f'<g transform="translate(0,{header_h})">')

    for y in range(y0, y1):
        for x in range(x0, x1):
            px, py = (x-x0)*tile, (y-y0)*tile
            v = grid[y][x]
            if v == EXTERIOR:
                continue
            elif v == WALL:
                if (x, y) in doors:
                    L.append(f'<rect x="{px}" y="{py}" width="{tile}" height="{tile}" fill="url(#p_floor)"/>')
                else:
                    ext = is_exterior_wall(grid, x, y, gh, gw)
                    L.append(f'<rect x="{px}" y="{py}" width="{tile}" height="{tile}" fill="url(#{"p_wext" if ext else "p_wall"})"/>')
            elif v == FLOOR:
                L.append(f'<rect x="{px}" y="{py}" width="{tile}" height="{tile}" fill="url(#p_floor)"/>')
            else:
                L.append(f'<rect x="{px}" y="{py}" width="{tile}" height="{tile}" fill="url(#p_corr)"/>')

    # Porte: varco con denti (stesso stile OLDSCHOOL)
    sw = max(1.5, tile * 0.08)
    stipite = max(2, tile // 3)
    used, door_groups = set(), []
    for (dx, dy), orient in sorted(doors.items()):
        if (dx, dy) in used: continue
        group = [(dx, dy)]; used.add((dx, dy))
        nx, ny = (dx, dy+1) if orient == 'h' else (dx+1, dy)
        while (nx, ny) in doors and doors[(nx,ny)] == orient and (nx,ny) not in used:
            group.append((nx,ny)); used.add((nx,ny))
            if orient == 'h': ny += 1
            else: nx += 1
        door_groups.append((group, orient))

    for group, orient in door_groups:
        gxs = [dx for dx,dy in group]; gys = [dy for dx,dy in group]
        px0 = (min(gxs)-x0)*tile; py0 = (min(gys)-y0)*tile
        px1 = (max(gxs)-x0)*tile+tile; py1 = (max(gys)-y0)*tile+tile
        if orient == 'h':
            for ax, ay in [(px0,py0),(px0,py1),(px1,py0),(px1,py1)]:
                dx2 = stipite if ax == px0 else -stipite
                L.append(f'<line x1="{ax}" y1="{ay}" x2="{ax+dx2}" y2="{ay}" stroke="#d4b870" stroke-width="{sw}"/>')
        else:
            for ax, ay in [(px0,py0),(px1,py0),(px0,py1),(px1,py1)]:
                dy2 = stipite if ay == py0 else -stipite
                L.append(f'<line x1="{ax}" y1="{ay}" x2="{ax}" y2="{ay+dy2}" stroke="#d4b870" stroke-width="{sw}"/>')

    fs = max(8, tile//3)
    for room in rooms:
        rx2, ry2, rw, rh = room['x'], room['y'], room['w'], room['h']
        cx = (rx2+rw/2-x0)*tile; cy = (ry2+rh/2-y0)*tile
        bw = len(room['id'])*fs*0.7
        L.append(f'<rect x="{cx-bw/2:.0f}" y="{cy-fs:.0f}" width="{bw:.0f}" height="{fs*1.4:.0f}" fill="rgba(0,0,0,0.55)" rx="3"/>')
        L.append(f'<text x="{cx:.1f}" y="{cy+fs*0.35:.1f}" text-anchor="middle" font-family="sans-serif" font-size="{fs}" font-weight="bold" fill="#f0d890">{room["id"]}</text>')

    L.append('</g>')
    L.append('</svg>')
    write_svg(output_path, L)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('input')
    p.add_argument('--tile-size', type=int, default=TILE, dest='tile_size')
    p.add_argument('--seed',      type=int, default=0)
    p.add_argument('--output',    default=None)
    args = p.parse_args()
    data = load_data(args.input)
    output = args.output or os.path.splitext(args.input)[0] + '_stone.svg'
    render(data, args.tile_size, output, args.seed or data.get('seed', 42))
    print(f'✓ {output}')


if __name__ == '__main__':
    main()
