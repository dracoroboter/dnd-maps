#!/usr/bin/env python3
"""Test visivo pentacolo demoniaco."""
import sys, os, importlib.util
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'templates', 'objects'))

def load_plugin(name):
    p = os.path.join(os.path.dirname(__file__), '..', 'templates', 'objects', f'{name}.py')
    spec = importlib.util.spec_from_file_location(name, p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

plugin = load_plugin('demonic_pentacle_oldschool')
tile = 32
pad = 30
ow, oh = 5*tile, 5*tile
W, H = pad*2 + ow, pad*2 + oh + 30

L = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}">',
     f'<rect width="{W}" height="{H}" fill="white"/>']
plugin.render({}, {}, pad, pad, ow, oh, tile, L)
L.append(f'<text x="{W//2}" y="{H-8}" text-anchor="middle" font-family="sans-serif" font-size="11">demonic_pentacle 5×5</text>')
L.append('</svg>')

with open('build/object_test_pentacle.svg','w') as f:
    f.write('\n'.join(L))
print('✓ build/object_test_pentacle.svg')
