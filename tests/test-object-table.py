#!/usr/bin/env python3
"""Test visivo oggetto tavolo."""
import sys, os, importlib.util
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'templates', 'objects'))

def load_plugin(name):
    p = os.path.join(os.path.dirname(__file__), '..', 'templates', 'objects', f'{name}.py')
    spec = importlib.util.spec_from_file_location(name, p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

table = load_plugin('table_oldschool')
large = load_plugin('large_table_oldschool')
tile = 32
pad = 20

items = [
    ('table',       table, 2, 1),
    ('large_table', large, 2, 4),
]

W = pad*2 + len(items) * (tile*4 + pad)
H = pad*2 + tile*4 + 50

L = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}">']
L.append(f'<rect width="{W}" height="{H}" fill="white"/>')
L.append(f'<text x="{W//2}" y="18" text-anchor="middle" font-family="sans-serif" font-size="13" font-weight="bold">Tavoli</text>')

for i, (name, plugin, sw, sh) in enumerate(items):
    ow, oh = sw*tile, sh*tile
    ox = pad + i*(tile*4+pad)
    oy = pad + 24 + (tile*4 - oh)//2
    L.append(f'<rect x="{ox}" y="{oy}" width="{ow}" height="{oh}" fill="white"/>')
    plugin.render({}, {}, ox, oy, ow, oh, tile, L)
    L.append(f'<text x="{ox+ow//2}" y="{oy+oh+18}" text-anchor="middle" font-family="sans-serif" font-size="11">{name}</text>')

L.append('</svg>')
with open('build/object_test_table.svg','w') as f:
    f.write('\n'.join(L))
print('✓ build/object_test_table.svg')
