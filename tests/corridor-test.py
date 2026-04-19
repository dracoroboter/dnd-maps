#!/usr/bin/env python3
"""
corridor-test.py — Mappa minimale di test: 2 stanze + 1 corridoio.

Layout (in quadretti):
  - C1: corridoio centrale, 2 quadretti largo x 10 lungo (verticale)
  - S1: stanza sinistra, 6x10
  - S2: stanza destra, 6x10
  - Porta esterna in cima a C1
  - Porta C1→S1 a metà corridoio (lato sinistro)
  - Porta C1→S2 a metà corridoio (lato destro)

Unità: 1 quadretto = 5ft = 1,5m
"""

import os, sys
sys.path.insert(0, os.path.dirname(__file__))

from PIL import Image, ImageDraw, ImageFont

EXTERIOR = 3
WALL     = 0
FLOOR    = 1
CORR     = 2

C_EXTERIOR = (255, 255, 255)
C_WALL_EXT = (30,  30,  30)
C_WALL_INT = (120, 115, 108)
C_HATCH_EXT = (15, 15, 15)
C_HATCH_INT = (90, 85, 80)
C_FLOOR    = (240, 230, 180)
C_CORR     = (220, 180, 120)
C_GRID     = (200, 190, 145)
C_DOOR     = (80,  50,  20)
C_LABEL    = (30,  20,  10)

CELL = 24  # pixel per quadretto

# ── Layout ────────────────────────────────────────────────────────────────────
# Griglia 20x16 quadretti
GW, GH = 20, 16

# Posizioni (x, y, w, h) in quadretti
# Margine esterno: 2 quadretti
C1 = (9, 2, 2, 10)   # corridoio: x=9, y=2, largo 2, lungo 10
S1 = (2, 3, 6, 8)    # stanza sinistra
S2 = (12, 3, 6, 8)   # stanza destra

# Porta esterna: cima del corridoio (y=2, x=9..10)
EXT_DOOR = [(9, 1), (10, 1)]  # celle sul muro esterno superiore del corridoio

# Porta C1→S1: lato sinistro del corridoio a metà (y=7)
DOOR_C1_S1 = [(8, 7)]   # muro tra S1 e C1

# Porta C1→S2: lato destro del corridoio a metà (y=7)
DOOR_C1_S2 = [(11, 7)]  # muro tra C1 e S2


def build_grid():
    grid = [[EXTERIOR] * GW for _ in range(GH)]

    def carve_room(rx, ry, rw, rh, cell_type):
        # Muro attorno
        for y in range(ry-1, ry+rh+1):
            for x in range(rx-1, rx+rw+1):
                if 0 <= y < GH and 0 <= x < GW and grid[y][x] == EXTERIOR:
                    grid[y][x] = WALL
        # Pavimento
        for y in range(ry, ry+rh):
            for x in range(rx, rx+rw):
                grid[y][x] = cell_type

    carve_room(*C1, CORR)
    carve_room(*S1, FLOOR)
    carve_room(*S2, FLOOR)

    # Porte
    for (px, py) in EXT_DOOR:
        grid[py][px] = EXTERIOR  # apertura nel muro esterno
    for (px, py) in DOOR_C1_S1:
        grid[py][px] = CORR
    for (px, py) in DOOR_C1_S2:
        grid[py][px] = CORR

    return grid


def _draw_hatch(draw, px, py, cell, color, spacing=4):
    for offset in range(-cell, cell*2, spacing):
        x1, y1 = px+offset, py
        x2, y2 = px+offset+cell, py+cell
        if x1 < px: y1 += px-x1; x1 = px
        if x2 > px+cell: y2 -= x2-(px+cell); x2 = px+cell
        if y1 < py or y2 > py+cell or y1 >= y2: continue
        draw.line([(x1,y1),(x2,y2)], fill=color, width=1)


def render(grid):
    W, H = GW*CELL, GH*CELL
    img = Image.new('RGB', (W, H), C_EXTERIOR)
    draw = ImageDraw.Draw(img)

    for y in range(GH):
        for x in range(GW):
            px, py = x*CELL, y*CELL
            v = grid[y][x]
            if v == EXTERIOR:
                draw.rectangle([px, py, px+CELL-1, py+CELL-1], fill=C_EXTERIOR)
            elif v == WALL:
                is_ext = any(
                    0 <= y+dy < GH and 0 <= x+dx < GW and grid[y+dy][x+dx] == EXTERIOR
                    for dy, dx in [(-1,0),(1,0),(0,-1),(0,1)]
                )
                if is_ext:
                    draw.rectangle([px, py, px+CELL-1, py+CELL-1], fill=C_WALL_EXT)
                    _draw_hatch(draw, px, py, CELL, C_HATCH_EXT, spacing=max(3, CELL//5))
                else:
                    draw.rectangle([px, py, px+CELL-1, py+CELL-1], fill=C_WALL_INT)
                    _draw_hatch(draw, px, py, CELL, C_HATCH_INT, spacing=max(3, CELL//5))
            else:
                color = C_FLOOR if v == FLOOR else C_CORR
                draw.rectangle([px, py, px+CELL-1, py+CELL-1], fill=color)
                draw.rectangle([px, py, px+CELL-1, py+CELL-1], outline=C_GRID)

    # Porte interne
    door_thick = max(2, CELL//6)
    door_len   = max(4, CELL*3//4)
    for (px_, py_) in DOOR_C1_S1 + DOOR_C1_S2:
        px, py = px_*CELL + CELL//2, py_*CELL + CELL//2
        # Porte orizzontali (muro verticale)
        draw.rectangle([px-door_thick, py-door_len//2, px+door_thick, py+door_len//2], fill=C_DOOR)

    # Etichette
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", CELL-4)
    except Exception:
        font = ImageFont.load_default()

    for label, (rx, ry, rw, rh) in [('C1', C1), ('S1', S1), ('S2', S2)]:
        cx = (rx + rw//2)*CELL
        cy = (ry + rh//2)*CELL
        bb = draw.textbbox((0,0), label, font=font)
        draw.text((cx-(bb[2]-bb[0])//2, cy-(bb[3]-bb[1])//2), label, fill=C_LABEL, font=font)

    return img


if __name__ == '__main__':
    grid = build_grid()
    img = render(grid)
    out = 'build/corridor_test.png'
    img.save(out)
    print(f'✓ {out}  ({img.width}x{img.height}px)')
    print('Struttura: S1 ←porta→ C1 ←porta→ S2, porta esterna in cima a C1')
