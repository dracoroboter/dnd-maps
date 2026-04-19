#!/usr/bin/env python3
"""
json-to-svg-oldschool.py v0.2 — Renderer SVG stile old-school D&D (B&W, hatching random).

COMPATIBILITÀ: generate-dungeon.py cell-grid-0.3+
USO: python3 renderers/v1/json-to-svg-oldschool.py <input.json> [--tile-size N] [--seed N] [--output FILE]
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

TILE = 20



def hatch_lines(cx, cy, tile, rng, density=18, ext=False):
    lines = []
    pad = 1
    for _ in range(density):
        x1 = cx + pad + rng.random() * (tile - pad*2)
        y1 = cy + pad + rng.random() * (tile - pad*2)
        angle = math.radians(40 + rng.random() * 20)
        length = tile * 0.25 + rng.random() * tile * 0.35
        x2 = max(cx+pad, min(cx+tile-pad, x1 + math.cos(angle)*length))
        y2 = max(cy+pad, min(cy+tile-pad, y1 + math.sin(angle)*length))
        sw = 0.6 if ext else 0.5
        op = 0.5 if ext else 0.85
        lines.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                     f'stroke="black" stroke-width="{sw}" opacity="{op}"/>')
    return lines


def render(data, tile, output_path, seed):
    rooms = data['rooms']
    enr_title = data.get('_enrichment', {}).get('title', '').strip()
    title = enr_title or data.get('title', 'Dungeon')
    year  = (data.get('generated') or '')[:4] or '2026'
    view  = data.get('_view', 'dm')
    gw, gh = get_grid_size(data)
    rng   = random.Random(seed)
    grid  = rebuild_grid(rooms, gw, gh)
    doors = get_passages(data)
    bb    = bounding_box(grid, gw, gh)
    if not bb:
        return
    x0, y0, x1, y1 = bb
    W, H, header_h = (x1-x0)*tile, (y1-y0)*tile, 48
    sw = max(1.5, tile * 0.12)  # spessore bordi

    L = []
    L.append('<?xml version="1.0" encoding="UTF-8"?>')
    L.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H+header_h}" viewBox="0 0 {W} {H+header_h}">')
    L.append(f'<rect width="{W}" height="{H+header_h}" fill="white"/>')
    view_label = {'dm': '[DM]', 'players': '[Players]'}.get(view, '')
    L.append(f'<text x="{W//2}" y="28" text-anchor="middle" font-family="Georgia,serif" font-size="20" font-weight="bold" fill="black">{title}  {view_label}</text>')
    L.append(f'<text x="{W//2}" y="42" text-anchor="middle" font-family="sans-serif" font-size="9" fill="#555">© {year} Dracosoft — CC BY</text>')
    L.append(f'<g transform="translate(0,{header_h})">')

    # Pre-compute hidden passages (secret hidden, or secret found in players view)
    enr_pre = data.get('_enrichment', {})
    gate_map = {(g['x'], g['y']): g for g in enr_pre.get('gates', [])}

    # Group consecutive passage cells (same orient, adjacent)
    passage_cells = sorted(doors.items())
    used = set()
    passage_groups = []
    for (dx, dy), orient in passage_cells:
        if (dx, dy) in used:
            continue
        group = [(dx, dy)]
        used.add((dx, dy))
        # orient='h': horizontal wall, cells adjacent horizontally (same y, x increases)
        # orient='v': vertical wall, cells adjacent vertically (same x, y increases)
        if orient == 'h':
            nx, ny = dx+1, dy
        else:
            nx, ny = dx, dy+1
        while (nx, ny) in doors and doors[(nx, ny)] == orient and (nx, ny) not in used:
            group.append((nx, ny))
            used.add((nx, ny))
            if orient == 'h': nx += 1
            else: ny += 1
        passage_groups.append((group, orient))

    # hidden_passages: all cells of a group whose gate is secret hidden/found(players)
    hidden_passages = set()
    for group, orient in passage_groups:
        gate = next((gate_map[c] for c in group if c in gate_map), None)
        if gate:
            gtype, state = gate.get('type','door'), gate.get('state','closed')
            if gtype == 'secret' and state == 'hidden':
                hidden_passages.update(group)
            if gtype == 'secret' and state == 'found' and view == 'players':
                hidden_passages.update(group)

    # Floor tiles (thin grid)
    for y in range(y0, y1):
        for x in range(x0, x1):
            if grid[y][x] in (FLOOR, CORR):
                px, py = (x-x0)*tile, (y-y0)*tile
                L.append(f'<rect x="{px}" y="{py}" width="{tile}" height="{tile}" fill="white" stroke="#ccc" stroke-width="0.4"/>')

    # Wall hatching (includes hidden passage cells — treated as wall)
    for y in range(y0, y1):
        for x in range(x0, x1):
            if grid[y][x] == WALL and ((x, y) not in doors or (x, y) in hidden_passages):
                px, py = (x-x0)*tile, (y-y0)*tile
                ext = is_exterior_wall(grid, x, y, gh, gw)
                L.extend(hatch_lines(px, py, tile, rng, density=14 if ext else 20, ext=ext))

    # Black borders between floor and wall (includes hidden passage cells)
    for y in range(y0, y1):
        for x in range(x0, x1):
            if grid[y][x] not in (FLOOR, CORR):
                continue
            px, py = (x-x0)*tile, (y-y0)*tile
            if y > 0    and grid[y-1][x] == WALL and ((x, y-1) not in doors or (x, y-1) in hidden_passages):
                L.append(f'<line x1="{px}" y1="{py}" x2="{px+tile}" y2="{py}" stroke="black" stroke-width="{sw}"/>')
            if y < gh-1 and grid[y+1][x] == WALL and ((x, y+1) not in doors or (x, y+1) in hidden_passages):
                L.append(f'<line x1="{px}" y1="{py+tile}" x2="{px+tile}" y2="{py+tile}" stroke="black" stroke-width="{sw}"/>')
            if x > 0    and grid[y][x-1] == WALL and ((x-1, y) not in doors or (x-1, y) in hidden_passages):
                L.append(f'<line x1="{px}" y1="{py}" x2="{px}" y2="{py+tile}" stroke="black" stroke-width="{sw}"/>')
            if x < gw-1 and grid[y][x+1] == WALL and ((x+1, y) not in doors or (x+1, y) in hidden_passages):
                L.append(f'<line x1="{px+tile}" y1="{py}" x2="{px+tile}" y2="{py+tile}" stroke="black" stroke-width="{sw}"/>')

    # Passages: wall opening with gate (door/portcullis/arch/secret)

    # Load gate plugin
    import importlib.util as _ilu2
    gate_plugin_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'templates', 'gates', 'gate_oldschool.py')
    _spec = _ilu2.spec_from_file_location('gate_oldschool', gate_plugin_path)
    _gate_mod = _ilu2.module_from_spec(_spec)
    _spec.loader.exec_module(_gate_mod)

    for group, orient in passage_groups:
        # Find gate on any cell of the group (fix: not only group[0])
        gate = None
        for cell in group:
            if cell in gate_map:
                gate = gate_map[cell]
                break
        gtype = gate.get('type', 'door') if gate else 'door'
        state = gate.get('state', 'closed') if gate else 'closed'

        # Hidden passage: already rendered as wall above, skip opening
        if any(c in hidden_passages for c in group):
            continue

        # Floor tiles for all cells in the group
        for (dx, dy) in group:
            if not (x0 <= dx < x1 and y0 <= dy < y1): continue
            px, py = (dx-x0)*tile, (dy-y0)*tile
            L.append(f'<rect x="{px}" y="{py}" width="{tile}" height="{tile}" fill="white" stroke="#ccc" stroke-width="0.4"/>')

        # Pixel bounding box of the group
        gxs = [dx for dx, dy in group]
        gys = [dy for dx, dy in group]
        gx0g, gy0g = min(gxs), min(gys)
        gx1g, gy1g = max(gxs), max(gys)
        ppx0 = (gx0g-x0)*tile;  ppy0 = (gy0g-y0)*tile
        ppx1 = (gx1g-x0)*tile + tile; ppy1 = (gy1g-y0)*tile + tile
        ppw, pph = ppx1-ppx0, ppy1-ppy0

        # Render gate
        _gate_mod.render_gate(gate or {'type':'door','state':'closed'}, orient,
                              ppx0, ppy0, ppw, pph, tile, sw, L)

    # ── Enrichment (windows and objects) ───────────────────────────────────────
    enr = data.get('_enrichment', {})

    # Windows: short dash on exterior wall
    # Rule: do not overlap existing passages
    door_positions = set((d['x'], d['y']) for d in data.get('passages', []))
    win_len = max(3, tile * 2 // 3)
    for win in enr.get('windows', []):
        room = next((r for r in rooms if r['id'] == win['room']), None)
        if not room:
            continue
        rx2, ry2, rw, rh = room['x'], room['y'], room['w'], room['h']
        wall = win.get('wall', 'bottom')
        # Compute wall cells and check no passage overlap
        if wall == 'bottom':
            wall_cells = [(rx2 + i, ry2 + rh) for i in range(rw)]
            if any(c in door_positions for c in wall_cells): continue
            wx = (rx2 + rw/2 - x0)*tile; wy = (ry2 + rh - y0)*tile
            L.append(f'<line x1="{wx-win_len//2}" y1="{wy}" x2="{wx+win_len//2}" y2="{wy}" stroke="white" stroke-width="{sw*1.5}"/>')
            L.append(f'<line x1="{wx-win_len//2}" y1="{wy}" x2="{wx+win_len//2}" y2="{wy}" stroke="black" stroke-width="{sw*0.5}" stroke-dasharray="2,2"/>')
        elif wall == 'top':
            wall_cells = [(rx2 + i, ry2 - 1) for i in range(rw)]
            if any(c in door_positions for c in wall_cells): continue
            wx = (rx2 + rw/2 - x0)*tile; wy = (ry2 - y0)*tile
            L.append(f'<line x1="{wx-win_len//2}" y1="{wy}" x2="{wx+win_len//2}" y2="{wy}" stroke="white" stroke-width="{sw*1.5}"/>')
            L.append(f'<line x1="{wx-win_len//2}" y1="{wy}" x2="{wx+win_len//2}" y2="{wy}" stroke="black" stroke-width="{sw*0.5}" stroke-dasharray="2,2"/>')
        elif wall == 'left':
            wall_cells = [(rx2 - 1, ry2 + i) for i in range(rh)]
            if any(c in door_positions for c in wall_cells): continue
            wx = (rx2 - x0)*tile; wy = (ry2 + rh/2 - y0)*tile
            L.append(f'<line x1="{wx}" y1="{wy-win_len//2}" x2="{wx}" y2="{wy+win_len//2}" stroke="white" stroke-width="{sw*1.5}"/>')
            L.append(f'<line x1="{wx}" y1="{wy-win_len//2}" x2="{wx}" y2="{wy+win_len//2}" stroke="black" stroke-width="{sw*0.5}" stroke-dasharray="2,2"/>')
        elif wall == 'right':
            wall_cells = [(rx2 + rw, ry2 + i) for i in range(rh)]
            if any(c in door_positions for c in wall_cells): continue
            wx = (rx2 + rw - x0)*tile; wy = (ry2 + rh/2 - y0)*tile
            L.append(f'<line x1="{wx}" y1="{wy-win_len//2}" x2="{wx}" y2="{wy+win_len//2}" stroke="white" stroke-width="{sw*1.5}"/>')
            L.append(f'<line x1="{wx}" y1="{wy-win_len//2}" x2="{wx}" y2="{wy+win_len//2}" stroke="black" stroke-width="{sw*0.5}" stroke-dasharray="2,2"/>')

    # Objects: load template and renderer plugin
    import json as _json, importlib.util as _ilu
    obj_templates = {}
    obj_plugins   = {}
    tpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'templates', 'objects')

    def get_tpl(t):
        if t not in obj_templates:
            p = os.path.join(tpl_dir, f'{t}.json')
            obj_templates[t] = _json.load(open(p)) if os.path.exists(p) else {'size':[1,1],'directional':False}
        return obj_templates[t]

    def get_plugin(t, style='oldschool'):
        key = f'{t}_{style}'
        if key not in obj_plugins:
            p = os.path.join(tpl_dir, f'{key}.py')
            if os.path.exists(p):
                spec = _ilu.spec_from_file_location(key, p)
                mod  = _ilu.module_from_spec(spec)
                spec.loader.exec_module(mod)
                obj_plugins[key] = mod
            else:
                obj_plugins[key] = None
        return obj_plugins[key]

    placed = []  # lista di (gx, gy, gx+sw, gy+sh) per check sovrapposizione

    # Normal objects first (below), allow_overlap last (on top, e.g. altar on pentacle)
    objects_sorted = sorted(enr.get('objects', []), key=lambda o: 1 if o.get('allow_overlap') else 0)

    for obj in objects_sorted:
        room = next((r for r in rooms if r['id'] == obj['room']), None)
        if not room:
            continue
        rx2, ry2, rw, rh = room['x'], room['y'], room['w'], room['h']
        t   = obj.get('type', 'chest')
        tpl = get_tpl(t)
        sw_obj, sh_obj = tpl['size']
        direction = obj.get('direction', 'south')
        if tpl.get('directional'):
            axis = tpl.get('directional_axis', 'perpendicular')
            if axis == 'perpendicular':
                if direction in ('east', 'west'):
                    sw_obj, sh_obj = sh_obj, sw_obj
            elif axis == 'parallel':
                if direction in ('north', 'south') and sh_obj > sw_obj:
                    sw_obj, sh_obj = sh_obj, sw_obj
                elif direction in ('east', 'west') and sw_obj > sh_obj:
                    sw_obj, sh_obj = sh_obj, sw_obj

        gx = rx2 + obj.get('x', 0)
        gy = ry2 + obj.get('y', 0)
        gx = max(rx2, min(rx2+rw-sw_obj, gx))
        gy = max(ry2, min(ry2+rh-sh_obj, gy))

        # Overlap check (skipped if allow_overlap=true)
        if not obj.get('allow_overlap', False):
            r2 = (gx, gy, gx+sw_obj, gy+sh_obj)
            overlap = any(
                r2[0] < p[2] and r2[2] > p[0] and r2[1] < p[3] and r2[3] > p[1]
                for p in placed
            )
            if overlap:
                print(f'  ⚠ oggetto {t} in {obj["room"]} ({gx},{gy}) sovrapposto — saltato')
                continue
            placed.append((gx, gy, gx+sw_obj, gy+sh_obj))

        ox = (gx - x0) * tile
        oy = (gy - y0) * tile
        ow, oh = sw_obj * tile, sh_obj * tile

        plugin = get_plugin(t)
        if plugin:
            plugin.render(obj, tpl, ox, oy, ow, oh, tile, L)

    # Room labels
    fs = max(7, tile-5)
    for room in rooms:
        rx2, ry2, rw, rh = room['x'], room['y'], room['w'], room['h']
        cx = (rx2+rw/2-x0)*tile
        cy = (ry2+rh/2-y0)*tile
        L.append(f'<text x="{cx:.1f}" y="{cy+fs*0.35:.1f}" text-anchor="middle" font-family="sans-serif" font-size="{fs}" fill="#333">{room["id"]}</text>')

    L.append('</g>')
    L.append('</svg>')
    write_svg(output_path, L)


def validate_enrichment(enr, data, enr_path=None):
    """Valida dungeon_enrichment.json contro dungeon_base.json. Scrive warning su file log."""
    import json as _j
    tpl_dir  = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'templates', 'objects')
    gate_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'templates', 'gates')
    rooms    = {r['id']: r for r in data.get('rooms', [])}
    passages = {(p['x'], p['y']) for p in data.get('passages', [])}
    warnings = []

    for g in enr.get('gates', []):
        gtype = g.get('type', '')
        state = g.get('state', '')
        tpl_path = os.path.join(gate_dir, f'{gtype}.json')
        if not os.path.exists(tpl_path):
            warnings.append(f'gate tipo sconosciuto: "{gtype}" ({g["x"]},{g["y"]})')
            continue
        tpl = _j.load(open(tpl_path))
        if state not in tpl.get('states', []):
            warnings.append(f'gate "{gtype}" stato non valido: "{state}" (validi: {tpl["states"]})')
        if (g['x'], g['y']) not in passages:
            warnings.append(f'gate ({g["x"]},{g["y"]}) non corrisponde a nessun passage')

    for obj in enr.get('objects', []):
        t    = obj.get('type', '')
        room = obj.get('room', '')
        tpl_path = os.path.join(tpl_dir, f'{t}.json')
        if not os.path.exists(tpl_path):
            warnings.append(f'oggetto tipo sconosciuto: "{t}" in {room}')
            continue
        if room not in rooms:
            warnings.append(f'oggetto "{t}": stanza "{room}" non esiste')
            continue
        r = rooms[room]
        tpl = _j.load(open(tpl_path))
        sw, sh = tpl['size']
        direction_v = obj.get('direction', 'south')
        if tpl.get('directional'):
            axis = tpl.get('directional_axis', 'perpendicular')
            if axis == 'perpendicular':
                if direction_v in ('east', 'west'):
                    sw, sh = sh, sw
            elif axis == 'parallel':
                if direction_v in ('north', 'south') and sh > sw:
                    sw, sh = sh, sw
                elif direction_v in ('east', 'west') and sw > sh:
                    sw, sh = sh, sw
        ox, oy = obj.get('x', 0), obj.get('y', 0)
        if ox < 0 or oy < 0 or ox + sw > r['w'] or oy + sh > r['h']:
            warnings.append(f'oggetto "{t}" in {room} ({ox},{oy} size {sw}×{sh}) fuori dai bounds ({r["w"]}×{r["h"]})')

    log_path = (os.path.splitext(enr_path)[0] + '_warnings.log') if enr_path else None
    if warnings and log_path:
        with open(log_path, 'w') as f:
            f.write('\n'.join(f'✗ {w}' for w in warnings) + '\n')
        print(f'  ⚠ {len(warnings)} warning(s) → {log_path}')
    elif log_path and os.path.exists(log_path):
        os.remove(log_path)  # nessun warning: rimuovi log precedente


def main():
    p = argparse.ArgumentParser()
    p.add_argument('input')
    p.add_argument('--tile-size',   type=int, default=TILE, dest='tile_size')
    p.add_argument('--seed',        type=int, default=0)
    p.add_argument('--enrichment',  default=None)
    p.add_argument('--output',      default=None)
    p.add_argument('--view',        default='dm', choices=['dm', 'players'])
    args = p.parse_args()
    data = load_data(args.input)
    if args.enrichment:
        import json
        enr = json.load(open(args.enrichment))
        validate_enrichment(enr, data, args.enrichment)
        data['_enrichment'] = enr
    data['_view'] = args.view
    output = args.output or os.path.splitext(args.input)[0] + '_oldschool.svg'
    render(data, args.tile_size, output, args.seed or data.get('seed', 42))
    print(f'✓ {output}')


if __name__ == '__main__':
    main()
