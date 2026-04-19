#!/usr/bin/env python3
"""
ddl-to-enrichment.py — Parses a .ddl file and produces dungeon_enrichment.json  (v0.2)

Grammar (DDL-spec.md v0.3) — block / indentation structure:

    # seed: N
    dungeon "title":
        <ID> [is a <template>]:
            has <type> at <position>
            door to <ID> is <state>

Usage:
    python3 ddl-rtl/ddl-to-enrichment.py example_crypt.ddl \\
        --dungeon dungeon_base.json \\
        --output dungeon_enrichment.json
"""

import json, re, sys, argparse, random, importlib.util
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent

# ---------------------------------------------------------------------------
# Import template-apply (hyphen in filename → importlib)
# ---------------------------------------------------------------------------

def _load_ta():
    spec = importlib.util.spec_from_file_location(
        "template_apply", SCRIPTS_DIR / "template-apply.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

ta = _load_ta()

# ---------------------------------------------------------------------------
# Gate helpers
# ---------------------------------------------------------------------------

GATE_STATE_MAP = {
    "open":       ("open",   "door"),
    "closed":     ("closed", "door"),
    "locked":     ("locked", "door"),
    "hidden":     ("hidden", "secret"),
    "portcullis": ("closed", "portcullis"),
    "arch":       ("open",   "arch"),
}


def room_wall_cells(room):
    """Return the set of grid cells that form the 1-cell wall border of a room."""
    rx, ry, rw, rh = room['x'], room['y'], room['w'], room['h']
    cells = set()
    for x in range(rx - 1, rx + rw + 1):
        cells.add((x, ry - 1))    # top wall row
        cells.add((x, ry + rh))   # bottom wall row
    for y in range(ry, ry + rh):  # sides (vertical, excluding corners)
        cells.add((rx - 1, y))    # left wall col
        cells.add((rx + rw, y))   # right wall col
    return cells


def find_passages_between(dungeon, id1, id2):
    """
    Return list of passage dicts from dungeon_base whose (x,y) lies on the
    shared wall between room id1 and room id2.
    """
    r1 = ta.get_room(dungeon, id1)
    r2 = ta.get_room(dungeon, id2)
    if not r1 or not r2:
        return []
    shared = room_wall_cells(r1) & room_wall_cells(r2)
    return [p for p in dungeon.get('passages', []) if (p['x'], p['y']) in shared]


# ---------------------------------------------------------------------------
# DDL block parser
# ---------------------------------------------------------------------------

# Patterns
RE_SEED      = re.compile(r'^#\s*seed:\s*(\d+)', re.IGNORECASE)
RE_DUNGEON   = re.compile(r'^dungeon\s+"([^"]+)"', re.IGNORECASE)
RE_ROOM      = re.compile(r'^(\w+)(?:\s+is\s+a\s+([\w_]+))?\s*:?\s*$', re.IGNORECASE)
RE_HAS       = re.compile(r'^has\s+(\S+)\s+at\s+(\S+)\s*$', re.IGNORECASE)
RE_DOOR_TO   = re.compile(r'^door\s+to\s+(\w+)\s+is\s+(\S+)\s*$', re.IGNORECASE)


def parse_ddl(source):
    """
    Returns (seed_or_None, dungeon_name_or_None, room_blocks, warnings).

    room_blocks: list of dicts:
        {
          'id':       str,
          'template': str or None,
          'has':      [(obj_type, position), ...],
          'doors':    [(target_id, state), ...],
        }
    """
    seed = None
    dungeon_name = None
    warnings = []

    # --- Collect (indent, stripped_line) pairs, extract seed ---
    lines = []
    for raw in source.splitlines():
        stripped = raw.lstrip()
        if not stripped:
            continue
        m = RE_SEED.match(stripped)
        if m:
            seed = int(m.group(1))
            continue
        if stripped.startswith('#'):
            continue
        indent = len(raw) - len(stripped)
        lines.append((indent, stripped.rstrip()))

    if not lines:
        return seed, dungeon_name, [], ["File is empty"]

    # --- Header: optional dungeon "name": ---
    idx = 0
    m = RE_DUNGEON.match(lines[0][1])
    if m:
        dungeon_name = m.group(1)
        idx = 1

    # --- Determine indent levels ---
    # The shallowest indent after the header = room level
    body_lines = lines[idx:]
    if not body_lines:
        return seed, dungeon_name, [], warnings

    room_indent = min(ind for ind, _ in body_lines)

    # --- Parse room blocks ---
    room_blocks = []
    current = None

    for indent, line in body_lines:
        if indent == room_indent:
            # Room header
            if current is not None:
                room_blocks.append(current)

            m = RE_ROOM.match(line)
            if not m:
                warnings.append(f"Unrecognized room header: '{line}'")
                current = None
                continue

            room_id  = m.group(1)
            template = m.group(2).lower() if m.group(2) else None
            current  = {'id': room_id, 'template': template, 'has': [], 'doors': []}

        elif indent > room_indent:
            # Body directive
            if current is None:
                warnings.append(f"Body line outside any room block: '{line}'")
                continue

            m = RE_HAS.match(line)
            if m:
                current['has'].append((m.group(1).lower(), m.group(2).lower()))
                continue

            m = RE_DOOR_TO.match(line)
            if m:
                current['doors'].append((m.group(1), m.group(2).lower()))
                continue

            warnings.append(f"Unrecognized body line in {current['id']}: '{line}'")

        else:
            warnings.append(f"Unexpected indent level: '{line}'")

    if current is not None:
        room_blocks.append(current)

    return seed, dungeon_name, room_blocks, warnings


# ---------------------------------------------------------------------------
# Apply room blocks
# ---------------------------------------------------------------------------

def apply_blocks(room_blocks, dungeon, global_seed):
    """
    Returns (objects, gates, warnings).
    objects: list of placement dicts {room, type, x, y [, direction]}
    gates:   list of gate dicts {x, y, state, type}
    """
    rng = random.Random(global_seed)
    all_objects = []
    placed_by_room = {}
    gates = []
    warnings = []

    for block in room_blocks:
        room_id  = block['id']
        template = block['template']

        room = ta.get_room(dungeon, room_id)
        if room is None:
            warnings.append(f"Room '{room_id}' not found in dungeon")
            continue

        # --- Level A: apply template ---
        if template:
            try:
                tpl = ta.get_room_template(template)
            except FileNotFoundError:
                warnings.append(f"Template '{template}' not found — skipping {room_id}")
                tpl = None

            if tpl:
                min_w = tpl.get("min_size", {}).get("w", 0)
                min_h = tpl.get("min_size", {}).get("h", 0)
                if room["w"] < min_w or room["h"] < min_h:
                    warnings.append(
                        f"Room {room_id} ({room['w']}x{room['h']}) smaller than "
                        f"template '{template}' minimum ({min_w}x{min_h})"
                    )
                room_seed = rng.randint(0, 2 ** 31)
                objs, warns = ta.apply_template(room, tpl, room_seed, dungeon)
                warnings.extend(warns)
                all_objects.extend(objs)
                placed_by_room.setdefault(room_id, []).extend(objs)
                print(f"  {room_id} is a {template}: placed {len(objs)} object(s)")

        # --- Level B: explicit objects ---
        for obj_type, position in block['has']:
            existing = placed_by_room.get(room_id, [])
            pos = ta.try_place(position, obj_type, room["w"], room["h"], existing, rng)
            if pos is None:
                warnings.append(
                    f"Could not place {obj_type} at '{position}' in {room_id}"
                )
                continue
            obj = {"room": room_id, "type": obj_type, **pos}
            all_objects.append(obj)
            placed_by_room.setdefault(room_id, []).append(obj)
            d = f" dir={obj['direction']}" if "direction" in obj else ""
            print(f"  {room_id} has {obj_type} at {position}: x={obj['x']}, y={obj['y']}{d}")

        # --- Gates ---
        for target_id, state_str in block['doors']:
            if state_str not in GATE_STATE_MAP:
                warnings.append(
                    f"Unknown gate state '{state_str}' for door {room_id}→{target_id}"
                )
                continue
            passages = find_passages_between(dungeon, room_id, target_id)
            if not passages:
                warnings.append(
                    f"No passage found between {room_id} and {target_id} — gate skipped"
                )
                continue
            state, gate_type = GATE_STATE_MAP[state_str]
            for p in passages:
                gates.append({"x": p["x"], "y": p["y"], "state": state, "type": gate_type})
            print(f"  door {room_id}→{target_id}: {gate_type} {state} "
                  f"({len(passages)} passage cell(s))")

    return all_objects, gates, warnings


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(
        description="Parse a .ddl file and produce dungeon_enrichment.json"
    )
    ap.add_argument("ddl",       help="Path to .ddl file")
    ap.add_argument("--dungeon", required=True, help="Path to dungeon_base.json")
    ap.add_argument("--output",  required=True, help="Output dungeon_enrichment.json path")
    ap.add_argument("--seed",    type=int, default=None,
                    help="Override seed (overrides # seed in file)")
    args = ap.parse_args()

    source  = Path(args.ddl).read_text(encoding="utf-8")
    dungeon = json.loads(Path(args.dungeon).read_text(encoding="utf-8"))

    seed, dungeon_name, room_blocks, parse_warnings = parse_ddl(source)

    if args.seed is not None:
        seed = args.seed
    if seed is None:
        seed = random.randint(0, 2 ** 31)
        print(f"No seed found — generated: {seed}  (add '# seed: {seed}' to reproduce)")

    title = dungeon_name or Path(args.ddl).stem
    print(f"Applying '{title}' (seed {seed})")

    objects, gates, apply_warnings = apply_blocks(room_blocks, dungeon, seed)

    for w in parse_warnings + apply_warnings:
        print(f"  WARNING: {w}", file=sys.stderr)

    # --- Build enrichment (idempotent: replace only rooms/gates touched here) ---
    output_path = Path(args.output)
    if output_path.exists():
        enrichment = json.loads(output_path.read_text(encoding="utf-8"))
    else:
        enrichment = {"base": Path(args.dungeon).name, "title": "", "gates": [], "objects": []}

    touched_rooms = {b['id'] for b in room_blocks}
    enrichment["objects"] = [
        o for o in enrichment.get("objects", [])
        if o.get("room") not in touched_rooms
    ]
    enrichment["objects"].extend(objects)

    # Rebuild gate set (touched passages replace previous)
    touched_passages = set()
    for b in room_blocks:
        for target_id, _ in b['doors']:
            for p in find_passages_between(dungeon, b['id'], target_id):
                touched_passages.add((p['x'], p['y']))

    touched_pairs = {
        frozenset([b['id'], t]) for b in room_blocks for t, _ in b['doors']
    }
    enrichment["gates"] = [
        g for g in enrichment.get("gates", [])
        if (g.get("x"), g.get("y")) not in touched_passages
        and frozenset([g.get("from"), g.get("to")]) not in touched_pairs
    ]
    enrichment["gates"].extend(gates)
    if dungeon_name:
        enrichment["title"] = dungeon_name

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(enrichment, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"Written: {len(objects)} object(s), {len(gates)} gate(s) → {output_path}")


if __name__ == "__main__":
    main()
