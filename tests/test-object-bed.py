#!/usr/bin/env python3
"""Test visivo oggetto letto."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'templates', 'objects'))
import importlib.util

def load_plugin(name):
    p = os.path.join(os.path.dirname(__file__), '..', 'templates', 'objects', f'{name}.py')
    spec = importlib.util.spec_from_file_location(name, p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

bed = load_plugin('bed_oldschool')
tile = 32
pad = 20
directions = ['north', 'south', 'east', 'west']
# Letto 1×2: in north/south sw=1,sh=2; in east/west sw=2,sh=1
W = pad*2 + len(directions) * (tile*2 + pad)
H = pad*2 + 2*(tile*2 + pad*2) + 40

L = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}">']
L.append(f'<rect width="{W}" height="{H}" fill="white"/>')
L.append(f'<text x="{W//2}" y="18" text-anchor="middle" font-family="sans-serif" font-size="13" font-weight="bold">Letto — 4 direzioni</text>')

for i, d in enumerate(directions):
    for j, sheet in enumerate(['plain', 'dots']):
        sw, sh = (1, 2) if d in ('north','south') else (2, 1)
        ow, oh = sw*tile, sh*tile
        ox = pad + i*(tile*2+pad)
        oy = pad + 24 + j*(tile*2+pad*2) + (tile*2 - oh)//2
        L.append(f'<rect x="{ox}" y="{oy}" width="{ow}" height="{oh}" fill="#eee"/>')
        bed.render({'direction': d, 'sheet_type': sheet}, {}, ox, oy, ow, oh, tile, L)
        if j == 0:
            L.append(f'<text x="{ox+ow//2}" y="{oy-4}" text-anchor="middle" font-family="sans-serif" font-size="11">{d}</text>')
        L.append(f'<text x="{ox+ow+4}" y="{oy+oh//2+4}" font-family="sans-serif" font-size="9" fill="#666">{sheet}</text>')

L.append('</svg>')
with open('build/object_test_bed.svg','w') as f:
    f.write('\n'.join(L))
print('✓ build/object_test_bed.svg')
