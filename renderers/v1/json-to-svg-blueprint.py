#!/usr/bin/env python3
"""
json-to-svg-blueprint.py v0.2 — Stile schizzo su carta a quadretti.

COMPATIBILITÀ: generate-dungeon.py cell-grid-0.3+
USO: python3 renderers/v1/json-to-svg-blueprint.py <input.json> [--tile-size N] [--seed N] [--output FILE]
"""

import argparse
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(__file__))
from dungeon_svg_core import (
    load_data, rebuild_grid, get_grid_size, get_passages,
    bounding_box, is_exterior_wall, write_svg,
    EXTERIOR, WALL, FLOOR, CORR
)

TILE = 24

C_PAPER   = '#f0f4ff'
C_GRID    = '#c8d4ee'
C_INK     = '#1a3a8e'
C_INK_LT  = '#4a6abf'
C_TITLE   = '#0d2255'


def jitter_line(x1, y1, x2, y2, rng, amp=1.2, segs=4):
    """Spezza una linea in segmenti con leggero jitter per effetto mano libera."""
    pts = [(x1, y1)]
    for i in range(1, segs):
        t = i / segs
        mx = x1 + (x2-x1)*t + rng.uniform(-amp, amp)
        my = y1 + (y2-y1)*t + rng.uniform(-amp, amp)
        pts.append((mx, my))
    pts.append((x2, y2))
    d = f'M {pts[0][0]:.1f},{pts[0][1]:.1f} ' + ' '.join(f'L {p[0]:.1f},{p[1]:.1f}' for p in pts[1:])
    return d


def hatch_rect(px, py, tile, rng, color, spacing=4, angle=50, opacity=0.9):
    """Hatching diagonale in un rettangolo."""
    lines = []
    rad = math.radians(angle)
    cos_a, sin_a = math.cos(rad), math.sin(rad)
    for offset in range(-tile, tile*2, spacing):
        x1 = px + offset
        y1 = py
        x2 = px + offset + tile * sin_a * 2
        y2 = py + tile
        # Clamp ai bordi del rettangolo
        def clamp_segment(ax, ay, bx, by):
            pts = []
            for t in [0, 1]:
                tx = ax + t*(bx-ax)
                ty = ay + t*(by-ay)
                if px <= tx <= px+tile and py <= ty <= py+tile:
                    pts.append((tx, ty))
            if len(pts) == 2:
                jx = rng.uniform(-0.4, 0.4)
                jy = rng.uniform(-0.4, 0.4)
                lines.append(f'<line x1="{pts[0][0]+jx:.1f}" y1="{pts[0][1]+jy:.1f}" '
                              f'x2="{pts[1][0]+jx:.1f}" y2="{pts[1][1]+jy:.1f}" '
                              f'stroke="{color}" stroke-width="0.7" opacity="{opacity}"/>')
        clamp_segment(x1, y1, x2, y2)
    return lines


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
    W, H, header_h = (x1-x0)*tile, (y1-y0)*tile, 56
    sw = max(1.2, tile * 0.1)

    L = []
    L.append('<?xml version="1.0" encoding="UTF-8"?>')
    L.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H+header_h}" viewBox="0 0 {W} {H+header_h}">')

    # Sfondo carta
    L.append(f'<rect width="{W}" height="{H+header_h}" fill="{C_PAPER}"/>')

    # Griglia carta millimetrata
    grid_spacing = tile
    for gx in range(0, W+1, grid_spacing):
        L.append(f'<line x1="{gx}" y1="0" x2="{gx}" y2="{H+header_h}" stroke="{C_GRID}" stroke-width="0.4"/>')
    for gy in range(0, H+header_h+1, grid_spacing):
        L.append(f'<line x1="0" y1="{gy}" x2="{W}" y2="{gy}" stroke="{C_GRID}" stroke-width="0.4"/>')

    # Header
    L.append(f'<text x="{W//2}" y="30" text-anchor="middle" '
             f'font-family="cursive,Georgia,serif" font-size="22" fill="{C_TITLE}">{title}</text>')
    L.append(f'<text x="{W//2}" y="48" text-anchor="middle" '
             f'font-family="cursive,sans-serif" font-size="10" fill="{C_INK_LT}">© {year} Dracosoft — CC BY</text>')

    L.append(f'<g transform="translate(0,{header_h})">')

    # Hatching muri
    for y in range(y0, y1):
        for x in range(x0, x1):
            if grid[y][x] != WALL or (x, y) in doors:
                continue
            px, py = (x-x0)*tile, (y-y0)*tile
            ext = is_exterior_wall(grid, x, y, gh, gw)
            color = C_INK if ext else C_INK_LT
            spacing = 3 if ext else 5
            L.extend(hatch_rect(px, py, tile, rng, color, spacing=spacing))

    # Bordi stanze (linee con jitter)
    for y in range(y0, y1):
        for x in range(x0, x1):
            if grid[y][x] not in (FLOOR, CORR):
                continue
            px, py = (x-x0)*tile, (y-y0)*tile
            if y > 0    and grid[y-1][x] == WALL and (x, y-1) not in doors:
                L.append(f'<path d="{jitter_line(px, py, px+tile, py, rng)}" stroke="{C_INK}" stroke-width="{sw}" fill="none"/>')
            if y < gh-1 and grid[y+1][x] == WALL and (x, y+1) not in doors:
                L.append(f'<path d="{jitter_line(px, py+tile, px+tile, py+tile, rng)}" stroke="{C_INK}" stroke-width="{sw}" fill="none"/>')
            if x > 0    and grid[y][x-1] == WALL and (x-1, y) not in doors:
                L.append(f'<path d="{jitter_line(px, py, px, py+tile, rng)}" stroke="{C_INK}" stroke-width="{sw}" fill="none"/>')
            if x < gw-1 and grid[y][x+1] == WALL and (x+1, y) not in doors:
                L.append(f'<path d="{jitter_line(px+tile, py, px+tile, py+tile, rng)}" stroke="{C_INK}" stroke-width="{sw}" fill="none"/>')

    # Porte: denti con jitter
    stipite = max(2, tile // 3)
    used, door_groups = set(), []
    for (dx, dy), orient in sorted(doors.items()):
        if (dx, dy) in used: continue
        group = [(dx, dy)]; used.add((dx, dy))
        nx, ny = (dx+1, dy) if orient == 'h' else (dx, dy+1)
        while (nx, ny) in doors and doors[(nx,ny)] == orient and (nx,ny) not in used:
            group.append((nx,ny)); used.add((nx,ny))
            if orient == 'h': nx += 1
            else: ny += 1
        door_groups.append((group, orient))

    for group, orient in door_groups:
        gxs = [dx for dx,dy in group]; gys = [dy for dx,dy in group]
        px0 = (min(gxs)-x0)*tile; py0 = (min(gys)-y0)*tile
        px1 = (max(gxs)-x0)*tile+tile; py1 = (max(gys)-y0)*tile+tile
        if orient == 'h':
            for ax, ay in [(px0,py0),(px0,py1),(px1,py0),(px1,py1)]:
                ex = ax + (stipite if ax == px0 else -stipite)
                L.append(f'<path d="{jitter_line(ax, ay, ex, ay, rng, amp=0.5)}" stroke="{C_INK}" stroke-width="{sw}" fill="none"/>')
        else:
            for ax, ay in [(px0,py0),(px1,py0),(px0,py1),(px1,py1)]:
                ey = ay + (stipite if ay == py0 else -stipite)
                L.append(f'<path d="{jitter_line(ax, ay, ax, ey, rng, amp=0.5)}" stroke="{C_INK}" stroke-width="{sw}" fill="none"/>')

    # Etichette corsivo
    fs = max(7, tile-4)
    for room in rooms:
        rx2, ry2, rw, rh = room['x'], room['y'], room['w'], room['h']
        cx = (rx2+rw/2-x0)*tile
        cy = (ry2+rh/2-y0)*tile
        L.append(f'<text x="{cx:.1f}" y="{cy+fs*0.35:.1f}" text-anchor="middle" '
                 f'font-family="cursive,sans-serif" font-size="{fs}" fill="{C_INK}">{room["id"]}</text>')

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
    output = args.output or os.path.splitext(args.input)[0] + '_blueprint.svg'
    render(data, args.tile_size, output, args.seed or data.get('seed', 42))
    print(f'✓ {output}')


if __name__ == '__main__':
    main()
