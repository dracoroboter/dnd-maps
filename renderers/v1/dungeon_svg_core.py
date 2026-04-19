"""
dungeon_svg_core.py — Modulo comune per i renderer SVG del dungeon.

Usato da: json-to-svg.py, json-to-svg-oldschool.py
"""

import json
import os

EXTERIOR = 3
WALL     = 0
FLOOR    = 1
CORR     = 2


def load_data(path):
    with open(path) as f:
        return json.load(f)


def rebuild_grid(rooms_data, gw, gh):
    grid = [[EXTERIOR] * gw for _ in range(gh)]
    for room in rooms_data:
        rx, ry, rw, rh = room['x'], room['y'], room['w'], room['h']
        cell_val = CORR if room['type'] == 'corridor' else FLOOR
        for y in range(ry-1, ry+rh+1):
            for x in range(rx-1, rx+rw+1):
                if 0 <= y < gh and 0 <= x < gw and grid[y][x] == EXTERIOR:
                    grid[y][x] = WALL
        for y in range(ry, ry+rh):
            for x in range(rx, rx+rw):
                if 0 <= y < gh and 0 <= x < gw:
                    grid[y][x] = cell_val
    return grid


def get_grid_size(data):
    gs = data.get('grid_size', '60x60')
    return map(int, gs.split('x'))


def get_passages(data):
    """Restituisce dict {(x,y): orient} dai passage nel JSON."""
    return {(d['x'], d['y']): d['orient'] for d in data.get('passages', [])}


def bounding_box(grid, gw, gh, margin=4):
    xs = [x for y in range(gh) for x in range(gw) if grid[y][x] != EXTERIOR]
    ys = [y for y in range(gh) for x in range(gw) if grid[y][x] != EXTERIOR]
    if not xs:
        return None
    return (
        max(0, min(xs)-margin),
        max(0, min(ys)-margin),
        min(gw, max(xs)+margin+1),
        min(gh, max(ys)+margin+1),
    )


def is_exterior_wall(grid, x, y, gh, gw):
    return any(
        0 <= y+dy < gh and 0 <= x+dx < gw and grid[y+dy][x+dx] == EXTERIOR
        for dy, dx in [(-1,0),(1,0),(0,-1),(0,1)]
    )


def svg_header(W, H, header_h, title, year):
    return [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H+header_h}" viewBox="0 0 {W} {H+header_h}">',
    ]


def svg_footer():
    return ['</svg>']


def write_svg(path, lines):
    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
