#!/usr/bin/env python3
import base64, sys, os
sys.path.insert(0, os.path.dirname(__file__))

TILESET = "goodExamples/kenney_scribble-dungeons/PNG/Default (64px)"
tile = 64

def b64(path):
    with open(path,'rb') as f:
        return 'data:image/png;base64,' + base64.b64encode(f.read()).decode()

t_door = b64(f"{TILESET}/door_open.png")

# Tutte le trasformazioni dentro <g> con translate per posizionare
def door_at(x, y, tr=""):
    # tr è relativa all'origine (0,0), poi traslata a (x,y)
    if tr:
        return f'<g transform="translate({x},{y})">\n  <g transform="{tr}"><image href="{t_door}" x="0" y="0" width="{tile}" height="{tile}"/></g>\n</g>'
    return f'<image href="{t_door}" x="{x}" y="{y}" width="{tile}" height="{tile}"/>'

cx, cy = tile//2, tile//2

variants = [
    ("1: normale",       ""),
    ("2: flipx",         f"scale(-1,1) translate(-{tile},0)"),
    ("3: flipy",         f"scale(1,-1) translate(0,-{tile})"),
    ("4: rot+90",        f"rotate(90,{cx},{cy})"),
    ("5: rot-90",        f"rotate(-90,{cx},{cy})"),
    ("6: rot180",        f"rotate(180,{cx},{cy})"),
    ("7: rot+90 flipx",  f"rotate(90,{cx},{cy}) scale(-1,1) translate(-{tile},0)"),
    ("8: rot-90 flipx",  f"rotate(-90,{cx},{cy}) scale(-1,1) translate(-{tile},0)"),
]

cols = 4
pad = 20
cell = tile + 50
W = cols * cell + pad*2
H = 2 * cell + pad*2 + 30

L = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}">']
L.append(f'<rect width="{W}" height="{H}" fill="white"/>')
L.append(f'<text x="{W//2}" y="20" text-anchor="middle" font-family="sans-serif" font-size="13" font-weight="bold">Quale numero per cella IN ALTO e quale per cella IN BASSO?</text>')

for i, (name, tr) in enumerate(variants):
    col = i % cols
    row = i // cols
    x = pad + col * cell
    y = pad + 30 + row * cell
    L.append(f'<rect x="{x}" y="{y}" width="{tile}" height="{tile}" fill="#e8e0d0" stroke="#999" stroke-width="1"/>')
    L.append(door_at(x, y, tr))
    L.append(f'<text x="{x+tile//2}" y="{y+tile+18}" text-anchor="middle" font-family="sans-serif" font-size="12" font-weight="bold">{name}</text>')

L.append('</svg>')

with open('build/door_test.svg','w') as f:
    f.write('\n'.join(L))
print('✓ build/door_test.svg')
