#!/usr/bin/env python3
"""
json-to-tmx.py — Converte il JSON strutturale del dungeon in formato Tiled Map Editor (.tmx)

Uso:
  python3 renderers/v1/json-to-tmx.py <input.json> [--tileset DIR] [--tile-size N] [--output FILE]

Il file .tmx può essere aperto in Tiled Map Editor (https://www.mapeditor.org/)
per applicare tileset grafici e aggiungere dettagli.

Layer generati:
  - exterior  : spazio esterno (tile vuoto)
  - walls     : muri (wall.png)
  - floor     : pavimento stanze e corridoi (floor.png)
  - doors     : porte (marcatore)
"""

import argparse
import json
import os
import xml.etree.ElementTree as ET
from xml.dom import minidom

# Valori griglia (devono corrispondere a generate-dungeon.py)
EXTERIOR = 3
WALL     = 0
FLOOR    = 1
CORR     = 2

# GID tileset (1-based in TMX)
GID_EMPTY = 0   # cella vuota
GID_FLOOR = 1   # floor.png
GID_WALL  = 2   # wall.png
GID_CORR  = 3   # floor_stone.png (corridoio)
GID_DOOR  = 4   # marcatore porta


def rebuild_grid(rooms_data, gw, gh):
    """Ricostruisce la griglia dal JSON."""
    grid = [[EXTERIOR] * gw for _ in range(gh)]

    for room in rooms_data:
        rx, ry, rw, rh = room['x'], room['y'], room['w'], room['h']
        cell_val = CORR if room['type'] == 'corridor' else FLOOR
        # Muro attorno
        for y in range(ry-1, ry+rh+1):
            for x in range(rx-1, rx+rw+1):
                if 0 <= y < gh and 0 <= x < gw and grid[y][x] == EXTERIOR:
                    grid[y][x] = WALL
        # Pavimento
        for y in range(ry, ry+rh):
            for x in range(rx, rx+rw):
                if 0 <= y < gh and 0 <= x < gw:
                    grid[y][x] = cell_val

    # Porte: celle CORR adiacenti a FLOOR (approssimazione)
    doors = set()
    for y in range(1, gh-1):
        for x in range(1, gw-1):
            if grid[y][x] == WALL:
                neighbors = [grid[y-1][x], grid[y+1][x], grid[y][x-1], grid[y][x+1]]
                if FLOOR in neighbors and CORR in neighbors:
                    doors.add((y, x))
                elif neighbors.count(FLOOR) >= 2:
                    # Muro tra due stanze con apertura
                    pass

    return grid, doors


def grid_to_tmx(grid, doors, gw, gh, tile_size, tileset_dir, output_path):
    """Genera il file TMX."""

    # ── Root map ──────────────────────────────────────────────────────────────
    map_el = ET.Element('map', {
        'version': '1.10',
        'tiledversion': '1.10.0',
        'orientation': 'orthogonal',
        'renderorder': 'right-down',
        'width': str(gw),
        'height': str(gh),
        'tilewidth': str(tile_size),
        'tileheight': str(tile_size),
        'infinite': '0',
        'nextlayerid': '5',
        'nextobjectid': '1',
    })

    # ── Tileset ───────────────────────────────────────────────────────────────
    ts = ET.SubElement(map_el, 'tileset', {
        'firstgid': '1',
        'name': 'dungeon',
        'tilewidth': str(tile_size),
        'tileheight': str(tile_size),
        'tilecount': '4',
        'columns': '1',
    })
    # Tile 0 (GID 1): floor
    t0 = ET.SubElement(ts, 'tile', {'id': '0'})
    ET.SubElement(t0, 'image', {
        'width': str(tile_size), 'height': str(tile_size),
        'source': os.path.join(tileset_dir, 'floor.png')
    })
    # Tile 1 (GID 2): wall
    t1 = ET.SubElement(ts, 'tile', {'id': '1'})
    ET.SubElement(t1, 'image', {
        'width': str(tile_size), 'height': str(tile_size),
        'source': os.path.join(tileset_dir, 'wall.png')
    })
    # Tile 2 (GID 3): floor_stone (corridoio)
    t2 = ET.SubElement(ts, 'tile', {'id': '2'})
    ET.SubElement(t2, 'image', {
        'width': str(tile_size), 'height': str(tile_size),
        'source': os.path.join(tileset_dir, 'floor_stone.png')
    })

    # ── Layer helper ──────────────────────────────────────────────────────────
    def make_layer(name, lid, data_list):
        layer = ET.SubElement(map_el, 'layer', {
            'id': str(lid), 'name': name,
            'width': str(gw), 'height': str(gh)
        })
        data = ET.SubElement(layer, 'data', {'encoding': 'csv'})
        rows = []
        for y in range(gh):
            row = ','.join(str(data_list[y][x]) for x in range(gw))
            rows.append(row)
        data.text = '\n' + '\n'.join(rows) + '\n'
        return layer

    # ── Costruisci layer ──────────────────────────────────────────────────────
    floor_data  = [[0]*gw for _ in range(gh)]
    wall_data   = [[0]*gw for _ in range(gh)]

    for y in range(gh):
        for x in range(gw):
            v = grid[y][x]
            if v == FLOOR:
                floor_data[y][x] = GID_FLOOR   # floor.png
            elif v == CORR:
                floor_data[y][x] = GID_CORR    # floor_stone.png
            elif v == WALL:
                wall_data[y][x] = GID_WALL     # wall.png

    make_layer('floor', 1, floor_data)
    make_layer('walls', 2, wall_data)

    # ── Serializza ────────────────────────────────────────────────────────────
    xml_str = ET.tostring(map_el, encoding='unicode')
    pretty = minidom.parseString(xml_str).toprettyxml(indent='  ')
    # Rimuovi la prima riga <?xml ...?> duplicata
    lines = pretty.split('\n')
    if lines[0].startswith('<?xml'):
        lines = lines[1:]
    result = '<?xml version="1.0" encoding="UTF-8"?>\n' + '\n'.join(lines)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(result)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('input', help='File JSON generato da generate-dungeon.py')
    p.add_argument('--tileset',   default='assets/tilesets/dcss')
    p.add_argument('--tile-size', type=int, default=16, dest='tile_size')
    p.add_argument('--grid-size', default='60x60', dest='grid_size')
    p.add_argument('--output',    default=None)
    args = p.parse_args()

    with open(args.input) as f:
        data = json.load(f)

    gw, gh = map(int, args.grid_size.split('x'))
    output = args.output or os.path.splitext(args.input)[0] + '.tmx'

    grid, doors = rebuild_grid(data['rooms'], gw, gh)
    grid_to_tmx(grid, doors, gw, gh, args.tile_size, args.tileset, output)
    print(f'✓ {output}  ({gw}x{gh} tiles, tileset: {args.tileset})')
    print(f'  Apri in Tiled Map Editor: https://www.mapeditor.org/')


if __name__ == '__main__':
    main()
