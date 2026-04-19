#!/usr/bin/env python3
"""
template-apply.py — Applies a room template to a dungeon room.

Reads dungeon_base.json and a room template JSON, runs the placement engine,
and writes (or updates) dungeon_enrichment.json.

Usage:
    python3 ddl-rtl/template-apply.py dungeon_base.json \\
        --room S4 --template bedroom [--seed 42] \\
        --output dungeon_enrichment.json

The placement engine:
  - Resolves object counts (fill strategy or linked-to-slot ratio)
  - Iterates placement preferences in seeded-random order
  - Checks object dimensions fit within room bounds
  - Checks no overlap with already-placed objects
  - Emits warnings for unfilled required slots
"""

import json
import argparse
import random
import re
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent
TEMPLATES_DIR = SCRIPTS_DIR.parent / "templates"
BUILD_DIR     = SCRIPTS_DIR.parent / "build"


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------

def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def get_object_template(obj_type):
    """Load templates/objects/<obj_type>.json. type may contain spaces (e.g. 'large_table')."""
    path = TEMPLATES_DIR / "objects" / f"{obj_type}.json"
    if not path.exists():
        raise FileNotFoundError(f"Object template not found: {path}")
    return load_json(path)


def get_room_template(template_name):
    path = BUILD_DIR / "rooms" / f"{template_name}.json"
    if not path.exists():
        raise FileNotFoundError(f"Room template not found: {path}")
    return load_json(path)


def get_room(dungeon, room_id):
    for room in dungeon["rooms"]:
        if room["id"] == room_id:
            return room
    return None


def door_walls(room, dungeon):
    """
    Return the set of wall directions ('north','south','east','west') that
    have at least one passage cell in dungeon_base.json.

    A passage at (px, py) belongs to a wall of room (rx, ry, rw, rh) when:
      north: py == ry - 1  and  rx <= px < rx + rw
      south: py == ry + rh and  rx <= px < rx + rw
      west:  px == rx - 1  and  ry <= py < ry + rh
      east:  px == rx + rw and  ry <= py < ry + rh
    """
    if dungeon is None:
        return set()
    rx, ry, rw, rh = room['x'], room['y'], room['w'], room['h']
    walls = set()
    for p in dungeon.get('passages', []):
        px, py = p['x'], p['y']
        if py == ry - 1     and rx <= px < rx + rw:
            walls.add('north')
        elif py == ry + rh  and rx <= px < rx + rw:
            walls.add('south')
        elif px == rx - 1   and ry <= py < ry + rh:
            walls.add('west')
        elif px == rx + rw  and ry <= py < ry + rh:
            walls.add('east')
    return walls


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------

def obj_dims(obj_type, direction=None):
    """
    Return (w, h) of an object, accounting for directional rotation.

    directional_axis controls which walls trigger rotation:
      "perpendicular" (default) — long side points away from wall (bed, bookcase head-on)
          → rotate when east/west
      "parallel" — long side runs along the wall (bookshelf, altar)
          → rotate so the longer dimension faces the wall direction:
             north/south wall (horizontal) → ensure w >= h
             east/west  wall (vertical)   → ensure h >= w
    """
    tpl = get_object_template(obj_type)
    w, h = tpl["size"]
    if not tpl.get("directional"):
        return w, h
    axis = tpl.get("directional_axis", "perpendicular")
    if axis == "perpendicular":
        if direction in ("east", "west"):
            return h, w
    elif axis == "parallel":
        if direction in ("north", "south") and h > w:
            return h, w   # rotate so long side is horizontal
        if direction in ("east", "west") and w > h:
            return h, w   # rotate so long side is vertical
    return w, h


def fits(x, y, w, h, room_w, room_h):
    return 0 <= x and x + w <= room_w and 0 <= y and y + h <= room_h


def overlaps(x, y, w, h, placed):
    """Return True if rectangle (x,y,w,h) overlaps any already-placed object."""
    for obj in placed:
        ow, oh = obj_dims(obj["type"], obj.get("direction"))
        ox, oy = obj["x"], obj["y"]
        if not (x + w <= ox or ox + ow <= x or y + h <= oy or oy + oh <= y):
            return True
    return False


# ---------------------------------------------------------------------------
# Position resolvers
# ---------------------------------------------------------------------------

def _place_near_wall(wall, distance, obj_type, room_w, room_h, placed, allow_overlap=False):
    """
    Core resolver: place obj_type at `distance` squares inward from the given wall,
    centered along that wall.
      distance=0  → touching the wall  (against_wall semantics)
      distance>0  → inset by that many squares  (near_wall semantics)
    Returns placement dict {x, y[, direction]} or None.
    """
    tpl = get_object_template(obj_type)
    direction = wall if tpl.get("directional") else None
    w, h = obj_dims(obj_type, direction)

    if wall == "north":
        x, y = (room_w - w) // 2, distance
    elif wall == "south":
        x, y = (room_w - w) // 2, room_h - h - distance
    elif wall == "east":
        x, y = room_w - w - distance, (room_h - h) // 2
    elif wall == "west":
        x, y = distance, (room_h - h) // 2
    else:
        return None

    if not fits(x, y, w, h, room_w, room_h):
        return None
    if not allow_overlap and overlaps(x, y, w, h, placed):
        return None

    result = {"x": x, "y": y}
    if direction:
        result["direction"] = direction
    return result


def _against_wall(wall, obj_type, room_w, room_h, placed, allow_overlap=False):
    """against_wall = near_wall at distance 0."""
    return _place_near_wall(wall, 0, obj_type, room_w, room_h, placed, allow_overlap)


def _near_wall(wall, obj_type, room_w, room_h, placed, rng, allow_overlap=False):
    """
    near_wall = distance 1 or 2, chosen at random (seeded).
    Tries both distances; if both fail prints a descriptive warning and returns None.
    """
    distances = [1, 2]
    rng.shuffle(distances)
    for d in distances:
        result = _place_near_wall(wall, d, obj_type, room_w, room_h, placed, allow_overlap)
        if result is not None:
            return result
    print(f"  WARNING: could not place {obj_type} near {wall} wall "
          f"(tried distances {distances[0]} and {distances[1]} — no free position)",
          file=sys.stderr)
    return None


def _beside(ref_type, obj_type, room_w, room_h, placed, rng, allow_overlap=False):
    """
    Place obj_type beside the long axis of already-placed ref_type objects.
    For a horizontal ref (rw >= rh): tries left and right positions, y-centered on ref.
    For a vertical ref  (rh >  rw): tries above and below positions, x-centered on ref.
    Falls back gracefully when neither position fits.
    """
    refs = [o for o in placed if o.get("type") == ref_type]
    if not refs:
        return None

    w, h = obj_dims(obj_type, None)
    candidates = []

    for ref in refs:
        rw, rh = obj_dims(ref["type"], ref.get("direction"))
        rx, ry = ref["x"], ref["y"]

        if rw >= rh:  # ref is horizontal → beside = left / right
            cy = ry + (rh - h) // 2
            candidates.append((rx - w,      cy))   # left
            candidates.append((rx + rw,     cy))   # right
        else:         # ref is vertical → beside = above / below
            cx = rx + (rw - w) // 2
            candidates.append((cx, ry - h))         # above
            candidates.append((cx, ry + rh))        # below

    rng.shuffle(candidates)
    for x, y in candidates:
        if not fits(x, y, w, h, room_w, room_h):
            continue
        if not allow_overlap and overlaps(x, y, w, h, placed):
            continue
        return {"x": x, "y": y}
    return None


def _next_to(ref_type, obj_type, room_w, room_h, placed, rng, allow_overlap=False):
    """
    Place obj_type adjacent (touching) to any already-placed object of ref_type.
    Generates all valid adjacent positions, shuffles them with the seeded rng,
    and returns the first that fits and does not overlap.
    """
    refs = [o for o in placed if o.get("type") == ref_type]
    if not refs:
        return None

    w, h = obj_dims(obj_type, None)

    candidates = []
    for ref in refs:
        rw, rh = obj_dims(ref["type"], ref.get("direction"))
        rx, ry = ref["x"], ref["y"]
        # left of ref
        for dy in range(-(h - 1), rh):
            candidates.append((rx - w, ry + dy))
        # right of ref
        for dy in range(-(h - 1), rh):
            candidates.append((rx + rw, ry + dy))
        # above ref
        for dx in range(-(w - 1), rw):
            candidates.append((rx + dx, ry - h))
        # below ref
        for dx in range(-(w - 1), rw):
            candidates.append((rx + dx, ry + rh))

    # deduplicate preserving order, then shuffle
    seen = set()
    unique = [c for c in candidates if not (c in seen or seen.add(c))]
    rng.shuffle(unique)

    for x, y in unique:
        if not fits(x, y, w, h, room_w, room_h):
            continue
        if not allow_overlap and overlaps(x, y, w, h, placed):
            continue
        return {"x": x, "y": y}

    return None


def _corner(corner, obj_type, room_w, room_h, placed, allow_overlap=False):
    """
    Try to place obj_type in the given corner (ne/nw/se/sw).
    Returns placement dict or None.
    """
    w, h = obj_dims(obj_type, None)
    corners = {
        "se": (room_w - w, room_h - h),
        "sw": (0,          room_h - h),
        "ne": (room_w - w, 0),
        "nw": (0,          0),
    }
    if corner not in corners:
        return None
    x, y = corners[corner]
    if not fits(x, y, w, h, room_w, room_h):
        return None
    if not allow_overlap and overlaps(x, y, w, h, placed):
        return None
    return {"x": x, "y": y}


def _center(obj_type, room_w, room_h, placed, allow_overlap=False):
    w, h = obj_dims(obj_type, None)
    x, y = (room_w - w) // 2, (room_h - h) // 2
    if not fits(x, y, w, h, room_w, room_h):
        return None
    if not allow_overlap and overlaps(x, y, w, h, placed):
        return None
    return {"x": x, "y": y}


def place_in_rows(obj_type, room_w, room_h, all_placed, max_count, gap=1, margin=1):
    """
    Place obj_type in parallel rows across the center of the room.
    Rows run along the longer room axis. Bookshelves in each pair of rows
    face each other (south/north or east/west) with a gap aisle between them.
    Returns list of placement dicts.
    """
    results = []

    if room_w >= room_h:
        # Horizontal rows: bookshelves face north/south → rotated to (w_long × 1)
        dir_a, dir_b = "south", "north"
        bw, bh = obj_dims(obj_type, dir_a)   # e.g. bookshelf: 2×1
        items_per_row = (room_w - 2 * margin) // bw
        if items_per_row < 1:
            return []
        # Each pair = row_a + gap + row_b; pairs separated by another gap
        pair_h = 2 * bh + gap
        n_pairs = max(1, (room_h - 2 * margin) // (pair_h + gap))
        total_h = n_pairs * pair_h + (n_pairs - 1) * gap
        start_y = (room_h - total_h) // 2
        total_w = items_per_row * bw
        start_x = (room_w - total_w) // 2
        for pi in range(n_pairs):
            base_y = start_y + pi * (pair_h + gap)
            for row_y, direction in [(base_y, dir_a), (base_y + bh + gap, dir_b)]:
                for ci in range(items_per_row):
                    if len(results) >= max_count:
                        return results
                    x, y = start_x + ci * bw, row_y
                    if fits(x, y, bw, bh, room_w, room_h):
                        fake_placed = all_placed + [{"type": obj_type, "x": r["x"], "y": r["y"],
                                                     "direction": r.get("direction")} for r in results]
                        if not overlaps(x, y, bw, bh, fake_placed):
                            results.append({"x": x, "y": y, "direction": direction})
    else:
        # Vertical rows: bookshelves face east/west → rotated to (1 × h_long)
        dir_a, dir_b = "east", "west"
        bw, bh = obj_dims(obj_type, dir_a)   # e.g. bookshelf: 1×2
        items_per_row = (room_h - 2 * margin) // bh
        if items_per_row < 1:
            return []
        pair_w = 2 * bw + gap
        n_pairs = max(1, (room_w - 2 * margin) // (pair_w + gap))
        total_w = n_pairs * pair_w + (n_pairs - 1) * gap
        start_x = (room_w - total_w) // 2
        total_h = items_per_row * bh
        start_y = (room_h - total_h) // 2
        for pi in range(n_pairs):
            base_x = start_x + pi * (pair_w + gap)
            for row_x, direction in [(base_x, dir_a), (base_x + bw + gap, dir_b)]:
                for ri in range(items_per_row):
                    if len(results) >= max_count:
                        return results
                    x, y = row_x, start_y + ri * bh
                    if fits(x, y, bw, bh, room_w, room_h):
                        fake_placed = all_placed + [{"type": obj_type, "x": r["x"], "y": r["y"],
                                                     "direction": r.get("direction")} for r in results]
                        if not overlaps(x, y, bw, bh, fake_placed):
                            results.append({"x": x, "y": y, "direction": direction})
    return results


def expand_any_prefs(prefs, rng, dw=None):
    """
    Expand wildcard entries into concrete variants (shuffled by rng).
    Used by the fill strategy so each specific position counts as a separate iteration.
      against_wall / against_wall_any    → 4 against_wall_<dir> entries
      against_wall_no_door               → against_wall_<dir> for walls without doors
      near_wall                          → 4 near_wall of <dir> entries
      near_wall_no_door                  → near_wall of <dir> for walls without doors
      corner / corner_any                → 4 corner_<c> entries
    All other entries are passed through unchanged.
    dw: set of wall directions occupied by doors (from door_walls()).
    """
    all_walls = ["south", "north", "east", "west"]
    corners   = ["se", "sw", "ne", "nw"]
    result    = []
    for p in prefs:
        norm = p.lower().strip()
        if norm in ("against_wall", "against_wall_any"):
            shuffled = all_walls[:]
            rng.shuffle(shuffled)
            result.extend(f"against_wall_{w}" for w in shuffled)
        elif norm == "against_wall_no_door":
            available = [w for w in all_walls if w not in (dw or set())]
            rng.shuffle(available)
            result.extend(f"against_wall_{w}" for w in available)
        elif norm == "near_wall":
            shuffled = all_walls[:]
            rng.shuffle(shuffled)
            result.extend(f"near_wall of {w}" for w in shuffled)
        elif norm == "near_wall_no_door":
            available = [w for w in all_walls if w not in (dw or set())]
            rng.shuffle(available)
            result.extend(f"near_wall of {w}" for w in available)
        elif norm in ("corner", "corner_any"):
            shuffled = corners[:]
            rng.shuffle(shuffled)
            result.extend(f"corner_{c}" for c in shuffled)
        else:
            result.append(p)
    return result


def try_place(preference, obj_type, room_w, room_h, placed, rng, allow_overlap=False, dw=None):
    """
    Try to place obj_type at the given preference string.
    Returns placement dict or None.
    Accepts both Italian (RTL source) and English (JSON) placement strings.
    Expands '_any' variants into a seeded-shuffled list of specific positions.
    allow_overlap=True skips the overlap check (used for objects layered on others).
    """
    p = preference.lower().strip()

    # --- Normalize shorthand forms → canonical ---
    # Core RTL (no suffix = any)
    if p == "against_wall":
        p = "against_wall_any"
    elif p == "corner":
        p = "corner_any"
    # Italian legacy (preprocessor not yet implemented)
    elif p == "contro il muro":
        p = "against_wall_any"
    elif p.startswith("contro il muro "):
        wall_map = {"nord": "north", "sud": "south", "est": "east", "ovest": "west"}
        wall_it = p[len("contro il muro "):]
        p = "against_wall_" + wall_map.get(wall_it, wall_it)
    elif p == "angolo":
        p = "corner_any"
    elif p.startswith("nell'angolo "):
        corner_map = {
            "nord-est": "ne", "nord-ovest": "nw",
            "sud-est":  "se", "sud-ovest":  "sw",
        }
        corner_it = p[len("nell'angolo "):]
        p = "corner_" + corner_map.get(corner_it, corner_it)
    elif p == "al centro":
        p = "center"

    # --- English canonical form ---
    if p == "against_wall_any":
        walls = ["south", "north", "east", "west"]
        rng.shuffle(walls)
        for wall in walls:
            result = _against_wall(wall, obj_type, room_w, room_h, placed, allow_overlap)
            if result is not None:
                return result
        return None

    if p == "against_wall_no_door":
        walls = [w for w in ["south", "north", "east", "west"] if w not in (dw or set())]
        rng.shuffle(walls)
        for wall in walls:
            result = _against_wall(wall, obj_type, room_w, room_h, placed, allow_overlap)
            if result is not None:
                return result
        return None

    if p.startswith("against_wall_"):
        wall = p[len("against_wall_"):]
        return _against_wall(wall, obj_type, room_w, room_h, placed, allow_overlap)

    # near_wall of <direction>  or  near_wall  (any wall)  or  near_wall_no_door
    m = re.match(r'^near_wall\s+of\s+(\w+)$', p)
    if m:
        return _near_wall(m.group(1), obj_type, room_w, room_h, placed, rng, allow_overlap)

    if p == "near_wall_no_door":
        walls = [w for w in ["south", "north", "east", "west"] if w not in (dw or set())]
        rng.shuffle(walls)
        for wall in walls:
            result = _near_wall(wall, obj_type, room_w, room_h, placed, rng, allow_overlap)
            if result is not None:
                return result
        return None

    if p == "near_wall":
        walls = ["south", "north", "east", "west"]
        rng.shuffle(walls)
        for wall in walls:
            result = _near_wall(wall, obj_type, room_w, room_h, placed, rng, allow_overlap)
            if result is not None:
                return result
        return None

    # beside <type>  (lungo l'asse lungo del riferimento)
    m = re.match(r'^beside\s+(\w+)$', p)
    if m:
        return _beside(m.group(1), obj_type, room_w, room_h, placed, rng, allow_overlap)

    # next_to <type>
    m = re.match(r'^next_to\s+(\w+)$', p)
    if m:
        return _next_to(m.group(1), obj_type, room_w, room_h, placed, rng, allow_overlap)

    if p == "corner_any":
        corners = ["se", "sw", "ne", "nw"]
        rng.shuffle(corners)
        for c in corners:
            result = _corner(c, obj_type, room_w, room_h, placed, allow_overlap)
            if result is not None:
                return result
        return None

    if p.startswith("corner_"):
        corner = p[len("corner_"):]
        return _corner(corner, obj_type, room_w, room_h, placed, allow_overlap)

    if p == "center":
        return _center(obj_type, room_w, room_h, placed, allow_overlap)

    print(f"  WARNING: unknown placement preference '{preference}'", file=sys.stderr)
    return None


# ---------------------------------------------------------------------------
# Placement engine
# ---------------------------------------------------------------------------

def apply_template(room, template, seed, dungeon=None):
    """
    Apply a room template to a room dict {id, w, h}.
    dungeon: full dungeon_base dict, used to detect door walls (L1).
    Returns (objects list, warnings list).
    """
    rng = random.Random(seed)
    placed_by_slot = {}   # slot_id -> list of placed obj dicts (with room key)
    all_placed = []       # all objects placed so far (for overlap checks)
    warnings = []
    dw = door_walls(room, dungeon)

    for slot in template["slots"]:
        slot_id       = slot["id"]
        obj_type      = slot["type"]
        required      = slot["required"]
        count_spec    = slot["count"]
        prefs         = slot["placement_preference"]
        allow_overlap = slot.get("allow_overlap", False)

        placed_by_slot[slot_id] = []

        # --- Resolve how many objects to place ---
        if "linked_to" in count_spec:
            ref_placed = placed_by_slot.get(count_spec["linked_to"], [])
            target = int(len(ref_placed) * count_spec["ratio"])
            min_count = 0
            max_count = target
        else:
            min_count = count_spec.get("min", 1)
            max_count = count_spec.get("max", 1)
            target    = max_count  # fill up to max

        # --- In-rows strategy: place object in parallel rows across room center ---
        if count_spec.get("strategy") == "in_rows":
            row_objs = place_in_rows(obj_type, room["w"], room["h"], all_placed, max_count)
            for pos in row_objs:
                obj = {"room": room["id"], "type": obj_type, **pos}
                all_placed.append(obj)
                placed_by_slot[slot_id].append(obj)

        # --- Fill strategy: iterate preferences, place one per hit ---
        # Expand _any variants into concrete positions (each counts separately).
        # Order within _any groups is seeded-random; multi-entry prefs keep their order.
        elif count_spec.get("strategy") == "fill":
            shuffled = expand_any_prefs(prefs, rng, dw)
            for pref in shuffled:
                if len(placed_by_slot[slot_id]) >= max_count:
                    break
                pos = try_place(pref, obj_type, room["w"], room["h"], all_placed, rng,
                                allow_overlap, dw)
                if pos is not None:
                    obj = {"room": room["id"], "type": obj_type, **pos}
                    if allow_overlap:
                        obj["allow_overlap"] = True
                    all_placed.append(obj)
                    placed_by_slot[slot_id].append(obj)

        # --- Linked or fixed count: try to place exactly target objects ---
        # Note: prefs order is a priority list — do NOT shuffle it.
        # Seeded randomness happens inside try_place for 'any' variants.
        elif count_spec.get("strategy") != "in_rows":
            for _ in range(target):
                placed_this = False
                for pref in prefs:
                    pos = try_place(pref, obj_type, room["w"], room["h"], all_placed, rng,
                                    allow_overlap, dw)
                    if pos is not None:
                        obj = {"room": room["id"], "type": obj_type, **pos}
                        if allow_overlap:
                            obj["allow_overlap"] = True
                        all_placed.append(obj)
                        placed_by_slot[slot_id].append(obj)
                        placed_this = True
                        break
                if not placed_this:
                    msg = (f"WARNING: could not place {obj_type} in {room['id']} "
                           f"(preferences exhausted: {prefs})")
                    warnings.append(msg)

        # --- Check minimum ---
        n_placed = len(placed_by_slot[slot_id])
        if required and n_placed < min_count:
            msg = (f"WARNING: required slot '{slot_id}' needs min {min_count} "
                   f"{obj_type} in {room['id']}, only placed {n_placed}")
            warnings.append(msg)

    return all_placed, warnings


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(
        description="Apply a room template to a dungeon room, writing dungeon_enrichment.json"
    )
    ap.add_argument("dungeon",   help="Path to dungeon_base.json")
    ap.add_argument("--room",     required=True, help="Room ID (e.g. S4)")
    ap.add_argument("--template", required=True, help="Template name (e.g. bedroom)")
    ap.add_argument("--seed",     type=int, default=42, help="Random seed (default: 42)")
    ap.add_argument("--output",   required=True, help="Output dungeon_enrichment.json path")
    args = ap.parse_args()

    dungeon = load_json(args.dungeon)
    room = get_room(dungeon, args.room)
    if room is None:
        print(f"ERROR: room '{args.room}' not found in {args.dungeon}", file=sys.stderr)
        sys.exit(1)

    template = get_room_template(args.template)

    # Check minimum room size
    min_w = template.get("min_size", {}).get("w", 0)
    min_h = template.get("min_size", {}).get("h", 0)
    if room["w"] < min_w or room["h"] < min_h:
        print(f"WARNING: room {args.room} ({room['w']}x{room['h']}) is smaller than "
              f"template minimum ({min_w}x{min_h})", file=sys.stderr)

    print(f"Applying template '{args.template}' to room {args.room} "
          f"({room['w']}x{room['h']}) with seed {args.seed}")

    objects, warnings = apply_template(room, template, args.seed)

    for w in warnings:
        print(w, file=sys.stderr)

    # Load existing enrichment or create a new one
    output_path = Path(args.output)
    if output_path.exists():
        enrichment = load_json(output_path)
    else:
        enrichment = {
            "base": Path(args.dungeon).name,
            "gates": [],
            "objects": []
        }

    # Replace objects for this room (idempotent re-runs)
    enrichment["objects"] = [
        o for o in enrichment.get("objects", [])
        if o.get("room") != args.room
    ]
    enrichment["objects"].extend(objects)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(enrichment, f, indent=2, ensure_ascii=False)

    print(f"Written {len(objects)} objects to {output_path}:")
    for obj in objects:
        direction = f" direction={obj['direction']}" if "direction" in obj else ""
        print(f"  {obj['type']:20s} x={obj['x']}, y={obj['y']}{direction}")


if __name__ == "__main__":
    main()
