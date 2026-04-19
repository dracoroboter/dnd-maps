#!/usr/bin/env python3
"""
generate-dungeon.py — Genera una mappa dungeon su griglia (BSP tree)
da passare a Gemini per la grafica finale.

Uso:
  python3 tech/scripts/generate-dungeon.py [opzioni] --output mappa.png

Opzioni struttura:
  --seed N              Seed (default: casuale)
  --rooms N             Numero stanze target (default: 8)
  --size WxH            Dimensione griglia in celle (default: 60x60)
  --dead-ends N         Vicoli ciechi aggiuntivi (default: 1)
  --wall-mode M         Modalità muri: dual, padding (default: dual)
                          dual:    celle pari=stanze, celle dispari=muri (1 cella fissa)
                          padding: muri spessi --wall-thickness celle attorno a ogni stanza
  --wall-thickness N    Spessore muri in celle, solo con --wall-mode padding (default: 1)
  --corridor-width N    Larghezza corridoi in celle, 1-4 (default: 1)

Opzioni stanze speciali:
  --entrance            Marca stanza di ingresso (verde)
  --boss                Marca stanza boss (rosso)
  --treasure            Marca stanza tesoro (giallo)
  --traps N             N stanze trappola (viola)

Opzioni grafiche:
  --cell-size N         Pixel per cella (default: 16, ignorato se --tileset)
  --walls W             Bordi: smooth, rough (default: smooth)
  --fill F              Pavimento: stone, brick, plain (default: stone)
  --tileset DIR         Directory con floor.png e wall.png (sovrascrive --fill)

Output:
  --output FILE         File PNG (default: dungeon.png)
  --json FILE           Struttura JSON (opzionale)
"""

import argparse
import random
import json
import os
from PIL import Image, ImageDraw, ImageFont

# ── Colori ───────────────────────────────────────────────────────────────────
C_WALL      = (30,  25,  20)
C_WALL_BG   = (55,  48,  42)   # sfondo muro (più chiaro del nero puro)
C_HATCH     = (20,  16,  12)   # colore linee hatching
C_FLOOR     = {'stone': (220, 210, 195), 'brick': (210, 175, 140), 'plain': (235, 225, 210)}
C_CORRIDOR  = {'stone': (200, 190, 175), 'brick': (190, 155, 120), 'plain': (215, 205, 190)}
C_GRID      = (170, 160, 148)  # colore griglia sul pavimento
C_BG        = (15,  12,  10)
C_SPECIAL   = {'entrance': (80, 160, 80), 'boss': (160, 50, 50),
               'treasure': (180, 150, 40), 'trap': (130, 60, 140)}
C_LABEL     = (30,  20,  10)
C_DOOR      = (60,  40,  20)   # colore porte

WALL  = 0
FLOOR = 1
CORR  = 2

# ── BSP tree ─────────────────────────────────────────────────────────────────

class BSPNode:
    def __init__(self, x, y, w, h):
        self.x, self.y, self.w, self.h = x, y, w, h
        self.left = self.right = None
        self.room = None  # (rx, ry, rw, rh)

    def split(self, rng, min_size=10, depth=0, max_depth=4):
        if self.left or self.right:
            self.left.split(rng, min_size, depth+1, max_depth)
            self.right.split(rng, min_size, depth+1, max_depth)
            return
        if depth >= max_depth:
            return
        # Decidi se splittare orizzontalmente o verticalmente
        horiz = rng.random() > 0.5
        if self.w > self.h * 1.25:
            horiz = False
        elif self.h > self.w * 1.25:
            horiz = True
        max_split = (self.h if horiz else self.w) - min_size
        if max_split <= min_size:
            return  # troppo piccolo
        split_at = rng.randint(min_size, max_split)
        if horiz:
            self.left  = BSPNode(self.x, self.y, self.w, split_at)
            self.right = BSPNode(self.x, self.y + split_at, self.w, self.h - split_at)
        else:
            self.left  = BSPNode(self.x, self.y, split_at, self.h)
            self.right = BSPNode(self.x + split_at, self.y, self.w - split_at, self.h)
        # Splitta ricorsivamente i figli appena creati
        self.left.split(rng, min_size, depth+1, max_depth)
        self.right.split(rng, min_size, depth+1, max_depth)

    def get_leaves(self):
        if not self.left and not self.right:
            return [self]
        leaves = []
        if self.left:  leaves += self.left.get_leaves()
        if self.right: leaves += self.right.get_leaves()
        return leaves

    def create_room(self, rng, padding=1, max_size=999):
        pad = max(1, padding)
        max_rw = min(max_size, max(4, self.w - pad * 2))
        min_rw = max(4, min(self.w * 2 // 3, max_rw))
        rw = rng.randint(min_rw, max_rw)
        max_rh = min(max_size, max(4, self.h - pad * 2))
        min_rh = max(4, min(self.h * 2 // 3, max_rh))
        rh = rng.randint(min_rh, max_rh)
        rx = self.x + rng.randint(pad, max(pad, self.w - rw - pad))
        ry = self.y + rng.randint(pad, max(pad, self.h - rh - pad))
        self.room = (rx, ry, rw, rh)

    def get_room(self):
        if self.room:
            return self.room
        lr = self.left.get_room()  if self.left  else None
        rr = self.right.get_room() if self.right else None
        if not lr: return rr
        if not rr: return lr
        return lr  # arbitrario

def carve_corridor(grid, r1, r2, rng, width=1):
    """Corridoio a L tra i bordi più vicini di due stanze."""
    gh, gw = len(grid), len(grid[0])

    # Trova il punto sul bordo di r1 più vicino al centro di r2, e viceversa
    def clamp(v, lo, hi): return max(lo, min(hi, v))

    # Centro r2 clampato dentro r1 (punto di uscita da r1)
    cx2, cy2 = r2[0] + r2[2] // 2, r2[1] + r2[3] // 2
    x1 = clamp(cx2, r1[0], r1[0] + r1[2] - 1)
    y1 = clamp(cy2, r1[1], r1[1] + r1[3] - 1)

    # Centro r1 clampato dentro r2 (punto di arrivo in r2)
    cx1, cy1 = r1[0] + r1[2] // 2, r1[1] + r1[3] // 2
    x2 = clamp(cx1, r2[0], r2[0] + r2[2] - 1)
    y2 = clamp(cy1, r2[1], r2[1] + r2[3] - 1)

    # Scava corridoio a L tra (x1,y1) e (x2,y2)
    if rng.random() > 0.5:
        for x in range(min(x1, x2), max(x1, x2) + 1):
            for dy in range(width):
                ny = y1 + dy
                if 0 <= ny < gh and grid[ny][x] == WALL:
                    grid[ny][x] = CORR
        for y in range(min(y1, y2), max(y1, y2) + 1):
            for dx in range(width):
                nx = x2 + dx
                if 0 <= nx < gw and grid[y][nx] == WALL:
                    grid[y][nx] = CORR
    else:
        for y in range(min(y1, y2), max(y1, y2) + 1):
            for dx in range(width):
                nx = x1 + dx
                if 0 <= nx < gw and grid[y][nx] == WALL:
                    grid[y][nx] = CORR
        for x in range(min(x1, x2), max(x1, x2) + 1):
            for dy in range(width):
                ny = y2 + dy
                if 0 <= ny < gh and grid[ny][x] == WALL:
                    grid[ny][x] = CORR

def connect_tree(node, grid, rng, width=1):
    if not node.left or not node.right:
        return
    connect_tree(node.left, grid, rng, width)
    connect_tree(node.right, grid, rng, width)
    r1 = node.left.get_room()
    r2 = node.right.get_room()
    if r1 and r2:
        carve_corridor(grid, r1, r2, rng, width)

# ── Generazione ───────────────────────────────────────────────────────────────

def generate(gw, gh, n_rooms, dead_ends, rng, wall_mode='dual', wall_thickness=1, corridor_width=1, max_room_size=999):
    grid = [[WALL] * gw for _ in range(gh)]

    if wall_mode == 'dual':
        return _generate_dual(gw, gh, n_rooms, dead_ends, rng, corridor_width)
    else:
        return _generate_padding(gw, gh, n_rooms, dead_ends, rng, wall_thickness, corridor_width, max_room_size)


def _generate_dual(gw, gh, n_rooms, dead_ends, rng, corridor_width):
    """
    Modalità dual: le stanze occupano celle pari (x,y con x%2==0, y%2==0),
    i muri sono le celle dispari tra loro. Muri sempre 1 cella.
    """
    import math
    grid = [[WALL] * gw for _ in range(gh)]
    lgw, lgh = gw // 2, gh // 2
    max_depth = max(2, math.ceil(math.log2(n_rooms + 1)))
    root = BSPNode(1, 1, lgw - 2, lgh - 2)
    root.split(rng, min_size=max(4, min(lgw, lgh) // (n_rooms + 1)), max_depth=max_depth)
    leaves = root.get_leaves()
    for leaf in leaves:
        leaf.create_room(rng, padding=1)

    # Scava stanze: coordinate logiche → fisiche (x*2, y*2)
    for leaf in leaves:
        rx, ry, rw, rh = leaf.room
        for y in range(ry, ry + rh):
            for x in range(rx, rx + rw):
                grid[y*2][x*2] = FLOOR

    # Connetti: corridoi su celle fisiche tra stanze
    _connect_tree_dual(root, grid, rng, corridor_width)

    rooms_logical = [leaf.room for leaf in leaves if leaf.room]
    # Converti in coordinate fisiche per il resto del codice
    rooms = [(rx*2, ry*2, rw*2, rh*2) for rx, ry, rw, rh in rooms_logical]

    # Vicoli ciechi
    for _ in range(dead_ends):
        for attempt in range(20):
            rx = rng.randint(1, lgw - 5) * 2
            ry = rng.randint(1, lgh - 5) * 2
            rw = rng.randint(2, 5) * 2
            rh = rng.randint(2, 5) * 2
            if all(grid[y][x] == WALL for y in range(ry, min(ry+rh, gh)) for x in range(rx, min(rx+rw, gw))):
                for y in range(ry, min(ry+rh, gh)):
                    for x in range(rx, min(rx+rw, gw)):
                        grid[y][x] = FLOOR
                nearest = min(rooms, key=lambda r: abs(r[0]+r[2]//2-(rx+rw//2)) + abs(r[1]+r[3]//2-(ry+rh//2)))
                carve_corridor(grid, (rx, ry, rw, rh), nearest, rng, corridor_width)
                rooms.append((rx, ry, rw, rh))
                break

    return grid, rooms


def _connect_tree_dual(node, grid, rng, corridor_width):
    if not node.left or not node.right:
        return
    _connect_tree_dual(node.left, grid, rng, corridor_width)
    _connect_tree_dual(node.right, grid, rng, corridor_width)
    r1 = node.left.get_room()
    r2 = node.right.get_room()
    if r1 and r2:
        # Converti in fisiche
        r1f = (r1[0]*2, r1[1]*2, r1[2]*2, r1[3]*2)
        r2f = (r2[0]*2, r2[1]*2, r2[2]*2, r2[3]*2)
        carve_corridor(grid, r1f, r2f, rng, corridor_width)


def _generate_padding(gw, gh, n_rooms, dead_ends, rng, wall_thickness, corridor_width, max_room_size=999):
    """
    Modalità padding: ogni stanza ha wall_thickness celle di muro attorno.
    Le stanze possono essere più grandi, i muri hanno spessore configurabile.
    """
    import math
    grid = [[WALL] * gw for _ in range(gh)]
    pad = wall_thickness
    # max_depth: 2^max_depth foglie ≈ n_rooms. min_size piccolo per permettere split.
    max_depth = max(2, math.ceil(math.log2(n_rooms + 1)))
    root = BSPNode(pad, pad, gw - pad*2, gh - pad*2)
    root.split(rng, min_size=max(5, min(gw, gh) // (n_rooms * 2)), max_depth=max_depth)
    leaves = root.get_leaves()
    for leaf in leaves:
        leaf.create_room(rng, padding=pad, max_size=max_room_size)
        rx, ry, rw, rh = leaf.room
        for y in range(ry, ry + rh):
            for x in range(rx, rx + rw):
                grid[y][x] = FLOOR
    connect_tree(root, grid, rng, corridor_width)
    rooms = [leaf.room for leaf in leaves if leaf.room]

    for _ in range(dead_ends):
        for attempt in range(20):
            rx = rng.randint(pad, gw - 8)
            ry = rng.randint(pad, gh - 8)
            rw = rng.randint(4, 8)
            rh = rng.randint(4, 8)
            if all(grid[y][x] == WALL for y in range(ry, min(ry+rh,gh)) for x in range(rx, min(rx+rw,gw))):
                for y in range(ry, min(ry+rh, gh)):
                    for x in range(rx, min(rx+rw, gw)):
                        grid[y][x] = FLOOR
                nearest = min(rooms, key=lambda r: abs(r[0]+r[2]//2-(rx+rw//2)) + abs(r[1]+r[3]//2-(ry+rh//2)))
                carve_corridor(grid, (rx, ry, rw, rh), nearest, rng, corridor_width)
                rooms.append((rx, ry, rw, rh))
                break

    return grid, rooms

# ── Rendering ─────────────────────────────────────────────────────────────────

def _draw_hatch(draw, px, py, cell, color, spacing=4):
    """Disegna hatching diagonale in un quadrato (px,py)-(px+cell,py+cell)."""
    for offset in range(-cell, cell * 2, spacing):
        x1 = px + offset
        y1 = py
        x2 = px + offset + cell
        y2 = py + cell
        # Clippa alle coordinate del quadrato
        if x1 < px:
            y1 += px - x1
            x1 = px
        if x2 > px + cell:
            y2 -= x2 - (px + cell)
            x2 = px + cell
        if y1 < py or y2 > py + cell or y1 >= y2:
            continue
        draw.line([(x1, y1), (x2, y2)], fill=color, width=1)


def _find_doors(grid):
    """Trova celle di giunzione corridoio-stanza (candidati porta)."""
    gh, gw = len(grid), len(grid[0])
    doors = set()
    for y in range(1, gh - 1):
        for x in range(1, gw - 1):
            if grid[y][x] != CORR:
                continue
            # Porta se il corridoio tocca una stanza su almeno un lato
            neighbors = [grid[y-1][x], grid[y+1][x], grid[y][x-1], grid[y][x+1]]
            if FLOOR in neighbors:
                doors.add((x, y))
    return doors


def render(grid, rooms, specials, cell, fill, walls, rng, tileset_dir=None):
    gh = len(grid)
    gw = len(grid[0])

    # Carica tile se tileset specificato
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

    fc = C_FLOOR[fill] if fill in C_FLOOR else C_FLOOR['stone']
    cc = C_CORRIDOR[fill] if fill in C_CORRIDOR else C_CORRIDOR['stone']

    # ── Passo 1: disegna pavimenti e muri ────────────────────────────────────
    for y in range(gh):
        for x in range(gw):
            px, py = x * cell, y * cell
            if grid[y][x] == WALL:
                if tile_wall:
                    img.paste(tile_wall, (px, py))
                else:
                    # Sfondo muro + hatching diagonale
                    draw.rectangle([px, py, px+cell-1, py+cell-1], fill=C_WALL_BG)
                    _draw_hatch(draw, px, py, cell, C_HATCH, spacing=max(3, cell//5))
            elif grid[y][x] in (FLOOR, CORR):
                if tile_floor:
                    img.paste(tile_floor, (px, py))
                else:
                    color = fc if grid[y][x] == FLOOR else cc
                    draw.rectangle([px, py, px+cell-1, py+cell-1], fill=color)
                    # Griglia leggera sul pavimento
                    draw.rectangle([px, py, px+cell-1, py+cell-1], outline=C_GRID)

    # ── Passo 2: colora stanze speciali ──────────────────────────────────────
    for rx, ry, rw, rh, sp in specials:
        color = C_SPECIAL[sp]
        for y in range(ry, ry + rh):
            for x in range(rx, rx + rw):
                px, py = x * cell, y * cell
                draw.rectangle([px, py, px+cell-1, py+cell-1], fill=color, outline=C_GRID)

    # ── Passo 3: porte ───────────────────────────────────────────────────────
    doors = _find_doors(grid)
    door_thick = max(2, cell // 6)
    door_len   = max(4, cell * 3 // 4)
    for (dx, dy) in doors:
        px, py = dx * cell + cell // 2, dy * cell + cell // 2
        # Determina orientamento: porta perpendicolare alla direzione del corridoio
        horiz_floor = (grid[dy][dx-1] == FLOOR or grid[dy][dx+1] == FLOOR) if 0 < dx < gw-1 else False
        if horiz_floor:
            # corridoio orizzontale → porta verticale
            draw.rectangle([px - door_thick, py - door_len//2,
                            px + door_thick, py + door_len//2], fill=C_DOOR)
        else:
            # corridoio verticale → porta orizzontale
            draw.rectangle([px - door_len//2, py - door_thick,
                            px + door_len//2, py + door_thick], fill=C_DOOR)

    # ── Passo 4: numeri stanze ───────────────────────────────────────────────
    try:
        font_size = max(10, cell - 2)
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
    except Exception:
        font = ImageFont.load_default()

    for i, room in enumerate(rooms):
        rx, ry, rw, rh = room
        cx = (rx + rw // 2) * cell
        cy = (ry + rh // 2) * cell
        label = str(i + 1)
        bbox = draw.textbbox((0, 0), label, font=font)
        tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
        draw.text((cx - tw//2, cy - th//2), label, fill=C_LABEL, font=font)

    # Legenda
    sp_types = list({s for _, _, _, _, s in specials})
    if sp_types:
        lx, ly = cell, H - cell * (len(sp_types) + 1)
        for sp in sp_types:
            draw.rectangle([lx, ly, lx+cell, ly+cell], fill=C_SPECIAL[sp])
            draw.text((lx + cell + 4, ly), sp, fill=C_LABEL, font=font)
            ly += cell + 4

    return img

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seed',           type=int, default=None)
    p.add_argument('--rooms',          type=int, default=8)
    p.add_argument('--size',           default='60x60')
    p.add_argument('--dead-ends',      type=int, default=1, dest='dead_ends')
    p.add_argument('--wall-mode',      default='dual', choices=['dual','padding'], dest='wall_mode')
    p.add_argument('--wall-thickness', type=int, default=1, dest='wall_thickness')
    p.add_argument('--corridor-width', type=int, default=2, dest='corridor_width',
                   help='Larghezza corridoi in celle, 1-4 (default: 2)')
    p.add_argument('--max-room',       type=int, default=15, dest='max_room',
                   help='Dimensione massima stanza in quadretti per lato (default: 15)')
    p.add_argument('--entrance',  action='store_true')
    p.add_argument('--boss',      action='store_true')
    p.add_argument('--treasure',  action='store_true')
    p.add_argument('--traps',     type=int, default=0)
    p.add_argument('--cell-size', type=int, default=16, dest='cell_size')
    p.add_argument('--walls',     default='smooth', choices=['smooth','rough'])
    p.add_argument('--fill',      default='stone',  choices=['stone','brick','plain'])
    p.add_argument('--tileset',   default=None)
    p.add_argument('--output',    default='dungeon.png')
    p.add_argument('--json',      default=None)
    args = p.parse_args()

    seed = args.seed if args.seed is not None else random.randint(0, 2**31)
    rng = random.Random(seed)
    gw, gh = map(int, args.size.split('x'))
    print(f"Seed: {seed}  Griglia: {gw}x{gh}  Stanze target: {args.rooms}  Wall-mode: {args.wall_mode}")

    grid, rooms = generate(gw, gh, args.rooms, args.dead_ends, rng,
                           wall_mode=args.wall_mode,
                           wall_thickness=args.wall_thickness,
                           corridor_width=max(1, min(4, args.corridor_width)),
                           max_room_size=args.max_room)

    # Assegna speciali
    specials = []
    sp_queue = []
    if args.entrance: sp_queue.append('entrance')
    if args.boss:     sp_queue.append('boss')
    if args.treasure: sp_queue.append('treasure')
    for _ in range(args.traps): sp_queue.append('trap')
    idxs = list(range(len(rooms)))
    rng.shuffle(idxs)
    for i, sp in enumerate(sp_queue):
        if i < len(idxs):
            r = rooms[idxs[i]]
            specials.append((*r, sp))

    img = render(grid, rooms, specials, args.cell_size, args.fill, args.walls, rng, args.tileset)
    img.save(args.output)
    print(f"✓ {args.output}  ({img.width}x{img.height}px, {len(rooms)} stanze)")

    if args.json:
        with open(args.json, 'w') as f:
            json.dump({'seed': seed, 'rooms': rooms, 'specials': specials}, f, indent=2)
        print(f"  JSON: {args.json}")

if __name__ == '__main__':
    main()
