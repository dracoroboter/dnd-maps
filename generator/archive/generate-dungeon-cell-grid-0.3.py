#!/usr/bin/env python3
"""
generate-dungeon.py — Genera una mappa dungeon su griglia (cell-grid)
da passare a Gemini per la grafica finale.

Approccio: griglia di celle-stanza separate da muri di 1 quadretto.
Le stanze adiacenti sono collegate da aperture nel muro condiviso.

Uso:
  python3 tech/scripts/generate-dungeon.py [opzioni] --output mappa.png

Opzioni struttura:
  --seed N              Seed (default: casuale)
  --rooms N             Numero stanze target (default: 12)
  --size WxH            Dimensione griglia in quadretti (default: 60x60)
  --room-min N          Dimensione minima stanza in quadretti per lato (default: 4)
  --room-max N          Dimensione massima stanza in quadretti per lato (default: 12)
  --corridor-width N    Larghezza aperture tra stanze, 1-3 (default: 2)

Opzioni stanze speciali:
  --entrance            Marca stanza di ingresso (verde)
  --boss                Marca stanza boss (rosso)
  --treasure            Marca stanza tesoro (giallo)
  --traps N             N stanze trappola (viola)

Opzioni grafiche:
  --cell-size N         Pixel per quadretto (default: 16, ignorato se --tileset)
  --tileset DIR         Directory con floor.png e wall.png

Output:
  --output FILE         File PNG (default: dungeon.png)
  --json FILE           Struttura JSON (opzionale)
"""

import argparse
import random
import json
import os
from PIL import Image, ImageDraw, ImageFont

# ── Costanti griglia ──────────────────────────────────────────────────────────
WALL     = 0   # muro interno (tra stanze)
FLOOR    = 1   # pavimento stanza
CORR     = 2   # apertura/corridoio
EXTERIOR = 3   # esterno al dungeon
WALL_EXT = 4   # muro esterno (tra stanza e esterno)

# ── Colori debug ──────────────────────────────────────────────────────────────
C_EXTERIOR    = (255, 255, 255)   # esterno: bianco
C_WALL_EXT    = (20,  20,  20)    # muro esterno: nero
C_WALL_INT    = (120, 115, 108)   # muro interno: grigio medio
C_HATCH_EXT   = (10,  10,  10)
C_HATCH_INT   = (90,  85,  80)
C_FLOOR       = (240, 230, 180)   # stanza: giallo chiaro
C_CORR        = (220, 180, 120)   # corridoio: arancione chiaro
C_GRID        = (200, 190, 145)
C_BG          = (255, 255, 255)
C_SPECIAL     = {'entrance': (80, 160, 80), 'boss': (160, 50, 50),
                 'treasure': (180, 150, 40), 'trap': (130, 60, 140)}
C_LABEL       = (30,  20,  10)
C_DOOR        = (80,  50,  20)

# ── Generazione griglia di celle ──────────────────────────────────────────────

def generate(gw, gh, n_rooms, rng, room_min=4, room_max=12, corridor_width=2, corridor_rows=1):
    grid = [[EXTERIOR] * gw for _ in range(gh)]

    # ── Passo 1: costruisci griglia di celle ──────────────────────────────────
    # Ogni N righe, inserisce una riga con altezza 1-2 (corridoio potenziale)
    cells = []
    cell_grid = []
    cell_types = []

    y = 1
    row_idx = 0
    corr_interval = max(2, n_rooms // max(1, corridor_rows))  # ogni N righe una riga-corridoio

    while y + 1 + 1 < gh:
        is_corr_row = (corridor_rows > 0 and row_idx > 0 and row_idx % corr_interval == 0)
        if is_corr_row:
            ch = rng.randint(1, 2)
        else:
            max_ch = min(room_max, gh - y - 1)
            if max_ch < room_min:
                break
            ch = rng.randint(room_min, max_ch)

        row_cells = []
        x = 1
        while x + 1 + 1 < gw:
            max_cw = min(room_max, gw - x - 1)
            if max_cw < room_min:
                break
            cw = rng.randint(room_min, max_cw)
            cells.append((x, y, cw, ch))
            cell_types.append('corridor' if is_corr_row else 'room')
            row_cells.append(len(cells) - 1)
            x += cw + 1
        if row_cells:
            cell_grid.append(row_cells)
        y += ch + 1
        row_idx += 1

    total_cells = len(cells)
    if total_cells == 0:
        return grid, [], []

    # ── Passo 2: mappa idx → (row, col) ──────────────────────────────────────
    idx_to_rc = {}
    for r, row_cells in enumerate(cell_grid):
        for c, idx in enumerate(row_cells):
            idx_to_rc[idx] = (r, c)

    def cell_at(r, c):
        if 0 <= r < len(cell_grid) and 0 <= c < len(cell_grid[r]):
            return cell_grid[r][c]
        return -1

    def neighbors(idx):
        r, c = idx_to_rc[idx]
        return [nb for nb in [cell_at(r-1,c), cell_at(r+1,c), cell_at(r,c-1), cell_at(r,c+1)] if nb != -1]

    # ── Passo 3: BFS per selezionare n_rooms celle connesse ───────────────────
    center_r = len(cell_grid) // 2
    center_c = len(cell_grid[center_r]) // 2 if cell_grid else 0
    start = cell_at(center_r, center_c)
    if start == -1:
        start = 0

    from collections import deque
    visited = []
    seen = {start}
    q = deque([start])

    while q and len(visited) < n_rooms:
        idx = q.popleft()
        visited.append(idx)
        nbs = neighbors(idx)
        rng.shuffle(nbs)
        for nb in nbs:
            if nb not in seen:
                seen.add(nb)
                q.append(nb)

    active = set(visited)

    # ── Passo 4: disegna muri e stanze attive ────────────────────────────────
    rooms = []
    corridors = []
    room_by_cell = {}

    for i, idx in enumerate(visited):
        x, y, cw, ch = cells[idx]
        ctype = cell_types[idx]
        for ry in range(y-1, y+ch+1):
            for rx in range(x-1, x+cw+1):
                if 0 <= ry < gh and 0 <= rx < gw and grid[ry][rx] == EXTERIOR:
                    grid[ry][rx] = WALL
        cell_val = CORR if ctype == 'corridor' else FLOOR
        for ry in range(y, y+ch):
            for rx in range(x, x+cw):
                if 0 <= ry < gh and 0 <= rx < gw:
                    grid[ry][rx] = cell_val
        r = {'id': f'S{i+1}', 'x': x, 'y': y, 'w': cw, 'h': ch, 'type': ctype, 'connections': []}
        # Rinomina corridoi come C1, C2...
        rooms.append(r)
        room_by_cell[idx] = r

    # Rinomina i corridoi con prefisso C
    corr_count = 0
    for r in rooms:
        if r['type'] == 'corridor':
            corr_count += 1
            r['id'] = f'C{corr_count}'
    # Rinomina le stanze con prefisso S
    room_count = 0
    for r in rooms:
        if r['type'] == 'room':
            room_count += 1
            r['id'] = f'S{room_count}'

    # ── Passo 4c: rimuovi muri tra celle-corridoio adiacenti ─────────────────
    # Due celle-corridoio adiacenti devono formare un unico spazio continuo
    for idx in visited:
        if cell_types[idx] != 'corridor':
            continue
        ax, ay, aw, ah = cells[idx]
        r, c = idx_to_rc[idx]
        for dr, dc in [(0,1),(1,0)]:  # solo destra e sotto per evitare duplicati
            nb = cell_at(r+dr, c+dc)
            if nb == -1 or nb not in active or cell_types[nb] != 'corridor':
                continue
            bx, by, bw, bh = cells[nb]
            if dr == 0:  # adiacenti orizzontalmente → rimuovi muro verticale tra loro
                wall_x = ax + aw  # colonna muro
                oy1, oy2 = max(ay, by), min(ay+ah, by+bh)
                for wy in range(oy1, oy2):
                    if 0 <= wy < gh and 0 <= wall_x < gw:
                        grid[wy][wall_x] = CORR
            else:  # adiacenti verticalmente → rimuovi muro orizzontale tra loro
                wall_y = ay + ah  # riga muro
                ox1, ox2 = max(ax, bx), min(ax+aw, bx+bw)
                for wx in range(ox1, ox2):
                    if 0 <= wall_y < gh and 0 <= wx < gw:
                        grid[wall_y][wx] = CORR
    # Flood-fill sulle celle CORR della griglia: celle contigue → stesso corridoio
    visited_corr = set()
    merged_corridors = []
    cid_counter = 0

    for start_y in range(gh):
        for start_x in range(gw):
            if grid[start_y][start_x] != CORR or (start_y, start_x) in visited_corr:
                continue
            # BFS per trovare tutte le celle CORR contigue
            component = []
            q = deque([(start_y, start_x)])
            while q:
                cy, cx = q.popleft()
                if (cy, cx) in visited_corr or grid[cy][cx] != CORR:
                    continue
                visited_corr.add((cy, cx))
                component.append((cy, cx))
                for dy, dx in [(-1,0),(1,0),(0,-1),(0,1)]:
                    ny, nx = cy+dy, cx+dx
                    if 0 <= ny < gh and 0 <= nx < gw and (ny,nx) not in visited_corr and grid[ny][nx] == CORR:
                        q.append((ny, nx))

            if not component:
                continue
            cid_counter += 1
            min_y = min(c[0] for c in component)
            max_y = max(c[0] for c in component)
            min_x = min(c[1] for c in component)
            max_x = max(c[1] for c in component)
            merged_room = {
                'id': f'C{cid_counter}',
                'x': min_x, 'y': min_y,
                'w': max_x - min_x + 1, 'h': max_y - min_y + 1,
                'type': 'corridor', 'connections': []
            }
            merged_corridors.append(merged_room)
            # Aggiorna room_by_cell: tutte le celle originali di tipo corridoio → merged_room
            for idx in list(room_by_cell.keys()):
                r = room_by_cell[idx]
                if r['type'] == 'corridor':
                    rx, ry, rw, rh = r['x'], r['y'], r['w'], r['h']
                    # Se almeno una cella di questa room è nella componente
                    if any((cy, cx) in set(component) for cy in range(ry, ry+rh) for cx in range(rx, rx+rw)):
                        room_by_cell[idx] = merged_room

    # Sostituisci i corridoi originali con quelli uniti
    rooms = [r for r in rooms if r['type'] != 'corridor'] + merged_corridors

    # ── Passo 5: costruisci spanning tree basato su adiacenza FISICA ──────────
    # Due stanze sono fisicamente adiacenti se condividono un muro (overlap ≥ 1)
    # Costruisce MST con BFS per garantire connessione minima senza cicli

    def physical_neighbors(idx_a):
        """Restituisce stanze in active fisicamente adiacenti a idx_a."""
        ax, ay, aw, ah = cells[idx_a]
        result = []
        r, c = idx_to_rc[idx_a]
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nb = cell_at(r+dr, c+dc)
            if nb == -1 or nb not in active:
                continue
            bx, by, bw, bh = cells[nb]
            if dr == 0:  # stessa riga → overlap verticale
                oy1, oy2 = max(ay, by), min(ay+ah, by+bh)
                if oy2 > oy1:
                    result.append(nb)
            else:  # stessa colonna → overlap orizzontale
                ox1, ox2 = max(ax, bx), min(ax+aw, bx+bw)
                if ox2 > ox1:
                    result.append(nb)
        return result

    # BFS per spanning tree fisico
    edges = []
    tree_seen = {visited[0]}
    tree_q = deque([visited[0]])
    while tree_q:
        idx = tree_q.popleft()
        nbs = physical_neighbors(idx)
        rng.shuffle(nbs)
        for nb in nbs:
            if nb not in tree_seen:
                tree_seen.add(nb)
                edges.append((idx, nb))
                tree_q.append(nb)

    # Stanze non raggiunte dall'albero fisico (nessun overlap con nessun vicino)
    # Le colleghiamo con corridoi a L verso la stanza più vicina raggiunta
    unreached = [idx for idx in visited if idx not in tree_seen]
    for idx in unreached:
        nearest = min(tree_seen, key=lambda i: abs(cells[i][0]-cells[idx][0]) + abs(cells[i][1]-cells[idx][1]))
        edges.append((nearest, idx))
        tree_seen.add(idx)

    # ── Passo 5: scava aperture tra stanze adiacenti ──────────────────────────
    for a, b in edges:
        if a not in active or b not in active:
            continue
        ax, ay, aw, ah = cells[a]
        bx, by, bw, bh = cells[b]
        ra, rb = idx_to_rc[a], idx_to_rc[b]
        ra_room = room_by_cell[a]
        rb_room = room_by_cell[b]
        if ra_room is rb_room:
            continue  # stesso vano dopo merge, nessuna apertura necessaria

        half = corridor_width // 2
        dr = rb[0] - ra[0]
        dc = rb[1] - ra[1]

        if ra[0] == rb[0]:
            wall_x = (ax + aw) if ax < bx else (bx + bw)
            oy1 = max(ay, by)
            oy2 = min(ay + ah, by + bh)
            mid_y = (oy1 + oy2) // 2 if oy2 > oy1 else (ay + ah//2)
            if abs(dc) == 1:
                if oy2 <= oy1:
                    # Nessun overlap: scava corridoio a L
                    # Punto di uscita da a: centro del lato verso b
                    start_y = ay + ah//2
                    start_x = wall_x - (1 if ax < bx else -1)
                    end_y = by + bh//2
                    end_x = wall_x + (1 if ax < bx else -1)
                    # Corridoio a L verticale con muri laterali
                    for y_ in range(min(start_y, end_y), max(start_y, end_y)+1):
                        if 0 <= y_ < gh and 0 <= wall_x < gw and grid[y_][wall_x] != FLOOR:
                            grid[y_][wall_x] = CORR
                        for side in (-1, corridor_width):
                            sx = wall_x + side
                            if 0 <= y_ < gh and 0 <= sx < gw and grid[y_][sx] == EXTERIOR:
                                grid[y_][sx] = WALL
                    cid = f'C{len(corridors)+1}'
                    corridors.append({'id': cid, 'connects': [ra_room['id'], rb_room['id']]})
                    conn = {'to': rb_room['id'], 'via': f'corridoio {cid}'}
                    if conn not in ra_room['connections']: ra_room['connections'].append(conn)
                    conn2 = {'to': ra_room['id'], 'via': f'corridoio {cid}'}
                    if conn2 not in rb_room['connections']: rb_room['connections'].append(conn2)
                    continue
                for dy in range(corridor_width):
                    wy = mid_y - half + dy
                    if 0 <= wy < gh and 0 <= wall_x < gw:
                        grid[wy][wall_x] = CORR
                conn = {'to': rb_room['id'], 'via': 'porta'}
                if conn not in ra_room['connections']: ra_room['connections'].append(conn)
                conn2 = {'to': ra_room['id'], 'via': 'porta'}
                if conn2 not in rb_room['connections']: rb_room['connections'].append(conn2)
            else:
                # Corridoio — usa mid_y già calcolato
                corr_mid_y = mid_y
                cid = f'C{len(corridors)+1}'
                cx1 = ax + aw if ax < bx else bx + bw
                cx2 = bx if ax < bx else ax
                for cx in range(cx1, cx2 + 1):
                    if 0 <= corr_mid_y < gh and 0 <= cx < gw:
                        if grid[corr_mid_y][cx] != FLOOR:
                            grid[corr_mid_y][cx] = CORR
                    for side in (-1, corridor_width):
                        sy = corr_mid_y + side
                        if 0 <= sy < gh and 0 <= cx < gw and grid[sy][cx] == EXTERIOR:
                            grid[sy][cx] = WALL
                corridors.append({'id': cid, 'connects': [ra_room['id'], rb_room['id']]})
                conn = {'to': rb_room['id'], 'via': f'corridoio {cid}'}
                if conn not in ra_room['connections']: ra_room['connections'].append(conn)
                conn2 = {'to': ra_room['id'], 'via': f'corridoio {cid}'}
                if conn2 not in rb_room['connections']: rb_room['connections'].append(conn2)
        else:
            wall_y = (ay + ah) if ay < by else (by + bh)
            ox1 = max(ax, bx)
            ox2 = min(ax + aw, bx + bw)
            mid_x = (ox1 + ox2) // 2 if ox2 > ox1 else (ax + aw//2)
            if abs(dr) == 1:
                if ox2 <= ox1:
                    # Nessun overlap: scava corridoio a L
                    # Corridoio a L orizzontale con muri laterali
                    for x_ in range(min(start_x, end_x), max(start_x, end_x)+1):
                        if 0 <= wall_y < gh and 0 <= x_ < gw and grid[wall_y][x_] != FLOOR:
                            grid[wall_y][x_] = CORR
                        for side in (-1, corridor_width):
                            sy = wall_y + side
                            if 0 <= sy < gh and 0 <= x_ < gw and grid[sy][x_] == EXTERIOR:
                                grid[sy][x_] = WALL
                    cid = f'C{len(corridors)+1}'
                    corridors.append({'id': cid, 'connects': [ra_room['id'], rb_room['id']]})
                    conn = {'to': rb_room['id'], 'via': f'corridoio {cid}'}
                    if conn not in ra_room['connections']: ra_room['connections'].append(conn)
                    conn2 = {'to': ra_room['id'], 'via': f'corridoio {cid}'}
                    if conn2 not in rb_room['connections']: rb_room['connections'].append(conn2)
                    continue
                for dx in range(corridor_width):
                    wx = mid_x - half + dx
                    if 0 <= wall_y < gh and 0 <= wx < gw:
                        grid[wall_y][wx] = CORR
                conn = {'to': rb_room['id'], 'via': 'porta'}
                if conn not in ra_room['connections']: ra_room['connections'].append(conn)
                conn2 = {'to': ra_room['id'], 'via': 'porta'}
                if conn2 not in rb_room['connections']: rb_room['connections'].append(conn2)
            else:
                # Corridoio
                corr_mid_x = mid_x
                cid = f'C{len(corridors)+1}'
                cy1 = ay + ah if ay < by else by + bh
                cy2 = by if ay < by else ay
                for cy in range(cy1, cy2 + 1):
                    if 0 <= cy < gh and 0 <= corr_mid_x < gw:
                        if grid[cy][corr_mid_x] != FLOOR:
                            grid[cy][corr_mid_x] = CORR
                    for side in (-1, corridor_width):
                        sx = corr_mid_x + side
                        if 0 <= cy < gh and 0 <= sx < gw and grid[cy][sx] == EXTERIOR:
                            grid[cy][sx] = WALL
                corridors.append({'id': cid, 'connects': [ra_room['id'], rb_room['id']]})
                conn = {'to': rb_room['id'], 'via': f'corridoio {cid}'}
                if conn not in ra_room['connections']: ra_room['connections'].append(conn)
                conn2 = {'to': ra_room['id'], 'via': f'corridoio {cid}'}
                if conn2 not in rb_room['connections']: rb_room['connections'].append(conn2)

    return grid, rooms, corridors


def add_entrance_door(grid, entrance_room):
    """
    Apre una porta sul muro esterno della stanza entrance.
    Cerca il lato della stanza che ha EXTERIOR a 2 celle di distanza
    (stanza → muro → esterno) e scava il muro.
    """
    gh, gw = len(grid), len(grid[0])
    rx, ry, rw, rh = entrance_room

    # Candidati: (wall_y, wall_x) per ogni lato della stanza
    candidates = []
    mid_x = rx + rw // 2
    mid_y = ry + rh // 2

    # Top
    if ry >= 2 and grid[ry-1][mid_x] == WALL and grid[ry-2][mid_x] == EXTERIOR:
        candidates.append((ry-1, mid_x))
    # Bottom
    if ry+rh+1 < gh and grid[ry+rh][mid_x] == WALL and grid[ry+rh+1][mid_x] == EXTERIOR:
        candidates.append((ry+rh, mid_x))
    # Left
    if rx >= 2 and grid[mid_y][rx-1] == WALL and grid[mid_y][rx-2] == EXTERIOR:
        candidates.append((mid_y, rx-1))
    # Right
    if rx+rw+1 < gw and grid[mid_y][rx+rw] == WALL and grid[mid_y][rx+rw+1] == EXTERIOR:
        candidates.append((mid_y, rx+rw))

    # Cerca lungo tutto il perimetro se il centro non funziona
    if not candidates:
        for x in range(rx, rx + rw):
            if ry >= 2 and grid[ry-1][x] == WALL and grid[ry-2][x] == EXTERIOR:
                candidates.append((ry-1, x)); break
        for x in range(rx, rx + rw):
            if ry+rh+1 < gh and grid[ry+rh][x] == WALL and grid[ry+rh+1][x] == EXTERIOR:
                candidates.append((ry+rh, x)); break
        for y in range(ry, ry + rh):
            if rx >= 2 and grid[y][rx-1] == WALL and grid[y][rx-2] == EXTERIOR:
                candidates.append((y, rx-1)); break
        for y in range(ry, ry + rh):
            if rx+rw+1 < gw and grid[y][rx+rw] == WALL and grid[y][rx+rw+1] == EXTERIOR:
                candidates.append((y, rx+rw)); break

    if candidates:
        wy, wx = candidates[0]
        grid[wy][wx] = EXTERIOR  # apertura visibile nel bordo nero


# ── Rendering ─────────────────────────────────────────────────────────────────

def _draw_hatch(draw, px, py, cell, color, spacing=4):
    for offset in range(-cell, cell * 2, spacing):
        x1, y1 = px + offset, py
        x2, y2 = px + offset + cell, py + cell
        if x1 < px: y1 += px - x1; x1 = px
        if x2 > px + cell: y2 -= x2 - (px + cell); x2 = px + cell
        if y1 < py or y2 > py + cell or y1 >= y2: continue
        draw.line([(x1, y1), (x2, y2)], fill=color, width=1)


def _find_doors(grid):
    gh, gw = len(grid), len(grid[0])
    doors = set()
    for y in range(1, gh - 1):
        for x in range(1, gw - 1):
            if grid[y][x] != CORR:
                continue
            if FLOOR in [grid[y-1][x], grid[y+1][x], grid[y][x-1], grid[y][x+1]]:
                doors.add((x, y))
    return doors


def render(grid, rooms, specials, cell, rng, tileset_dir=None, title=None):
    gh, gw = len(grid), len(grid[0])

    tile_floor = tile_wall = None
    if tileset_dir:
        try:
            tf = Image.open(os.path.join(tileset_dir, 'floor.png')).convert('RGB')
            tw = Image.open(os.path.join(tileset_dir, 'wall.png')).convert('RGB')
            cell = tf.width
            tile_floor = tf.resize((cell, cell))
            tile_wall  = tw.resize((cell, cell))
        except Exception as e:
            print(f"  Attenzione: tileset non caricato ({e}), uso colori flat")

    W, H = gw * cell, gh * cell
    img = Image.new('RGB', (W, H), C_BG)
    draw = ImageDraw.Draw(img)

    for y in range(gh):
        for x in range(gw):
            px, py = x * cell, y * cell
            v = grid[y][x]
            if v == EXTERIOR:
                draw.rectangle([px, py, px+cell-1, py+cell-1], fill=C_EXTERIOR)
            elif v == WALL:
                # Muro esterno se adiacente a EXTERIOR, altrimenti interno
                is_ext = any(
                    0 <= y+dy < len(grid) and 0 <= x+dx < len(grid[0]) and grid[y+dy][x+dx] == EXTERIOR
                    for dy, dx in [(-1,0),(1,0),(0,-1),(0,1)]
                )
                if is_ext:
                    draw.rectangle([px, py, px+cell-1, py+cell-1], fill=C_WALL_EXT)
                    _draw_hatch(draw, px, py, cell, C_HATCH_EXT, spacing=max(3, cell//5))
                else:
                    draw.rectangle([px, py, px+cell-1, py+cell-1], fill=C_WALL_INT)
                    _draw_hatch(draw, px, py, cell, C_HATCH_INT, spacing=max(3, cell//5))
            elif v == WALL_EXT:
                draw.rectangle([px, py, px+cell-1, py+cell-1], fill=C_WALL_EXT)
                _draw_hatch(draw, px, py, cell, C_HATCH_EXT, spacing=max(3, cell//5))
            else:
                color = C_FLOOR if v == FLOOR else C_CORR
                if tile_floor:
                    img.paste(tile_floor, (px, py))
                else:
                    draw.rectangle([px, py, px+cell-1, py+cell-1], fill=color)
                    draw.rectangle([px, py, px+cell-1, py+cell-1], outline=C_GRID)

    # Stanze speciali
    for rx, ry, rw, rh, sp in specials:
        color = C_SPECIAL[sp]
        for y in range(ry, ry + rh):
            for x in range(rx, rx + rw):
                px, py = x * cell, y * cell
                draw.rectangle([px, py, px+cell-1, py+cell-1], fill=color, outline=C_GRID)

    # Porte
    doors = _find_doors(grid)
    door_thick = max(2, cell // 6)
    door_len   = max(4, cell * 3 // 4)
    for (dx, dy) in doors:
        px, py = dx * cell + cell // 2, dy * cell + cell // 2
        horiz_floor = (grid[dy][dx-1] == FLOOR or grid[dy][dx+1] == FLOOR) if 0 < dx < gw-1 else False
        if horiz_floor:
            draw.rectangle([px-door_thick, py-door_len//2, px+door_thick, py+door_len//2], fill=C_DOOR)
        else:
            draw.rectangle([px-door_len//2, py-door_thick, px+door_len//2, py+door_thick], fill=C_DOOR)

    # Etichette stanze (S1, S2...) e corridoi (C1, C2...)
    try:
        font_size = max(10, cell - 2)
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
    except Exception:
        font = ImageFont.load_default()

    for room in rooms:
        cx = (room['x'] + room['w'] // 2) * cell
        cy = (room['y'] + room['h'] // 2) * cell
        label = room['id']
        bbox = draw.textbbox((0, 0), label, font=font)
        tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
        draw.text((cx - tw//2, cy - th//2), label, fill=C_LABEL, font=font)

    # ── Crop al bounding box del dungeon + margine, poi centra su canvas ──────
    margin = cell * 3
    min_x = min((x for y in range(gh) for x in range(gw) if grid[y][x] != EXTERIOR), default=0)
    max_x = max((x for y in range(gh) for x in range(gw) if grid[y][x] != EXTERIOR), default=gw-1)
    min_y = min((y for y in range(gh) for x in range(gw) if grid[y][x] != EXTERIOR), default=0)
    max_y = max((y for y in range(gh) for x in range(gw) if grid[y][x] != EXTERIOR), default=gh-1)

    crop_box = (
        max(0, min_x * cell - margin),
        max(0, min_y * cell - margin),
        min(W, (max_x + 1) * cell + margin),
        min(H, (max_y + 1) * cell + margin),
    )
    cropped = img.crop(crop_box)
    cw, ch = cropped.size

    # Header: titolo + copyright
    import datetime
    header_h = cell * 4
    footer_h = 0
    canvas_size = max(cw, ch) + margin * 2
    canvas = Image.new('RGB', (canvas_size, canvas_size + header_h + footer_h), C_EXTERIOR)
    ox = (canvas_size - cw) // 2
    canvas.paste(cropped, (ox, header_h + (canvas_size - ch) // 2))

    if title:
        cdraw = ImageDraw.Draw(canvas)
        # Titolo grande
        try:
            tfont = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", cell * 2)
        except Exception:
            tfont = ImageFont.load_default()
        tbbox = cdraw.textbbox((0, 0), title, font=tfont)
        tx = (canvas_size - (tbbox[2] - tbbox[0])) // 2
        cdraw.text((tx, cell // 2), title, fill=(30, 20, 10), font=tfont)

        # Copyright + data
        try:
            sfont = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", max(10, cell - 2))
        except Exception:
            sfont = ImageFont.load_default()
        year = datetime.date.today().year
        copy_text = f"© {year} Dracosoft — CC BY"
        cbbox = cdraw.textbbox((0, 0), copy_text, font=sfont)
        cx_ = (canvas_size - (cbbox[2] - cbbox[0])) // 2
        cdraw.text((cx_, cell * 2 + cell // 2), copy_text, fill=(100, 90, 80), font=sfont)

    return canvas


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seed',           type=int, default=None)
    p.add_argument('--rooms',          type=int, default=12)
    p.add_argument('--size',           default='60x60')
    p.add_argument('--room-min',       type=int, default=4,  dest='room_min')
    p.add_argument('--room-max',       type=int, default=12, dest='room_max')
    p.add_argument('--corridor-width', type=int, default=2,  dest='corridor_width')
    p.add_argument('--corridor-rows',  type=int, default=2,  dest='corridor_rows',
                   help='Numero di righe della griglia da generare come corridoi (default: 2)')
    p.add_argument('--entrance',  action='store_true')
    p.add_argument('--boss',      action='store_true')
    p.add_argument('--treasure',  action='store_true')
    p.add_argument('--traps',     type=int, default=0)
    p.add_argument('--title',     default=None)
    p.add_argument('--cell-size', type=int, default=16, dest='cell_size')
    p.add_argument('--tileset',   default=None)
    p.add_argument('--output',    default='dungeon.png')
    p.add_argument('--json',      default=None)
    args = p.parse_args()

    seed = args.seed if args.seed is not None else random.randint(0, 2**31)
    rng = random.Random(seed)
    gw, gh = map(int, args.size.split('x'))
    print(f"Seed: {seed}  Griglia: {gw}x{gh}  Stanze target: {args.rooms}")

    grid, rooms, corridors = generate(gw, gh, args.rooms, rng,
                           room_min=args.room_min,
                           room_max=args.room_max,
                           corridor_width=max(1, min(3, args.corridor_width)),
                           corridor_rows=args.corridor_rows)

    specials = []
    # Stanze speciali disabilitate temporaneamente — da riabilitare dopo fix grafica
    # (entrance, boss, treasure, trap verranno assegnati manualmente in futuro)

    # Porta verso l'esterno: sulla stanza con più esposizione all'esterno
    def exterior_exposure(room):
        rx, ry, rw, rh = room['x'], room['y'], room['w'], room['h']
        count = 0
        for x in range(rx, rx+rw):
            if ry >= 2 and grid[ry-2][x] == EXTERIOR: count += 1
            if ry+rh+1 < len(grid) and grid[ry+rh+1][x] == EXTERIOR: count += 1
        for y in range(ry, ry+rh):
            if rx >= 2 and grid[y][rx-2] == EXTERIOR: count += 1
            if rx+rw+1 < len(grid[0]) and grid[y][rx+rw+1] == EXTERIOR: count += 1
        return count

    best_entrance = max(rooms, key=exterior_exposure, default=None)
    if best_entrance and exterior_exposure(best_entrance) > 0:
        add_entrance_door(grid, (best_entrance['x'], best_entrance['y'], best_entrance['w'], best_entrance['h']))
        best_entrance['connections'].append({'to': 'esterno', 'via': 'porta esterna'})

    # Rileva porte esterne su tutti i vani
    for room in rooms:
        if room is best_entrance:
            continue
        rx, ry, rw, rh = room['x'], room['y'], room['w'], room['h']
        has_ext = False
        for x in range(rx, rx+rw):
            if ry > 0 and grid[ry-1][x] == EXTERIOR: has_ext = True
            if ry+rh < len(grid) and grid[ry+rh][x] == EXTERIOR: has_ext = True
        for y in range(ry, ry+rh):
            if rx > 0 and grid[y][rx-1] == EXTERIOR: has_ext = True
            if rx+rw < len(grid[0]) and grid[y][rx+rw] == EXTERIOR: has_ext = True
        if has_ext:
            conn = {'to': 'esterno', 'via': 'porta esterna'}
            if conn not in room['connections']:
                room['connections'].append(conn)

    img = render(grid, rooms, specials, args.cell_size, rng, args.tileset, title=args.title)
    img.save(args.output)
    print(f"✓ {args.output}  ({img.width}x{img.height}px, {len(rooms)} stanze, {len(corridors)} corridoi)")

    # Genera JSON struttura
    base = os.path.splitext(args.output)[0]
    json_path = args.json if args.json else base + '.json'
    import datetime
    structure = {
        'seed': seed, 'title': args.title,
        'generated': datetime.date.today().isoformat(),
        'rooms': rooms,
        'corridors': corridors,
    }
    with open(json_path, 'w') as f:
        json.dump(structure, f, indent=2, ensure_ascii=False)
    print(f"  JSON: {json_path}")

    # Genera MD descrizione
    md_path = base + '.md'
    with open(md_path, 'w') as f:
        t = args.title or 'Dungeon'
        f.write(f"# {t}\n\n")
        f.write(f"*Generato il {datetime.date.today().isoformat()} — seed {seed} — © Dracosoft CC BY*\n\n")
        f.write("---\n\n")
        for r in rooms:
            f.write(f"## {r['id']}\n\n")
            sp = r.get('special', '')
            if sp: f.write(f"*Tipo: {sp}*\n\n")
            f.write(f"Dimensioni: {r['w']}x{r['h']} quadretti ({r['w']*1.5:.0f}x{r['h']*1.5:.0f}m).\n\n")
            if r['connections']:
                conns = ', '.join(f"{c['to']} ({c['via']})" for c in r['connections'])
                f.write(f"Connessioni: {conns}.\n\n")
            else:
                f.write("Connessioni: nessuna — stanza isolata o segreta.\n\n")
            f.write("*Descrizione: da completare.*\n\n")
            f.write("---\n\n")
        for c in corridors:
            f.write(f"## {c['id']}\n\n")
            f.write(f"Corridoio tra {c['connects'][0]} e {c['connects'][1]}.\n\n")
            f.write("*Descrizione: da completare.*\n\n")
            f.write("---\n\n")
    print(f"  MD:   {md_path}")

if __name__ == '__main__':
    main()
