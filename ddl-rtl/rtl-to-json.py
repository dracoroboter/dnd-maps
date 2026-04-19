#!/usr/bin/env python3
"""
rtl-to-json.py — Compiles core RTL room template to JSON  (v0.3)

Core RTL grammar:

    template "name":
        min_size: WxH

        <type> required N to M fill: <placements>
        <type> optional N per <type>:  <placements>

        constraints: <list>
        todo:        <list>

Keywords:  template  min_size  required  optional  to  fill  per  constraints  todo
Types and placements are free strings (validated downstream by template-apply.py).
The colon before placements is mandatory.

Usage:
    python3 ddl-rtl/rtl-to-json.py templates/rooms/bedroom.rtl
    python3 ddl-rtl/rtl-to-json.py templates/rooms/bedroom.rtl -o out.json

Default output: build/rooms/<stem>.json
"""

import json, re, sys, argparse
from pathlib import Path

BUILD_ROOMS = Path(__file__).parent.parent / "build" / "rooms"

KEYWORDS = {'required', 'optional', 'overlap', 'fill', 'per', 'to', 'constraints', 'todo', 'min_size', 'template'}


def slot_id(type_str):
    return type_str + "s"


def parse_count(tokens, warnings):
    """
    Parse count tokens (list of lowercase strings).

    Fill:   ['1', 'to', '2', 'fill']   →  {min, max, strategy:'fill'}
    Linked: ['1', 'per', 'bed']        →  {linked_to:'beds', ratio:1}
    """
    # Fill: N to M fill  |  In-rows: N to M in_rows
    if len(tokens) >= 4 and tokens[1] == 'to' and tokens[3] in ('fill', 'in_rows'):
        try:
            mn, mx = int(tokens[0]), int(tokens[2])
        except ValueError:
            warnings.append(f"Invalid fill count values: '{tokens[0]}', '{tokens[2]}'")
            return None
        return {"min": mn, "max": mx, "strategy": tokens[3]}

    # Linked: N per <type>
    if len(tokens) >= 3 and tokens[1] == 'per':
        try:
            ratio = int(tokens[0])
        except ValueError:
            warnings.append(f"Invalid ratio: '{tokens[0]}'")
            return None
        ref_type = '_'.join(tokens[2:])   # multi-word type joined with underscore
        return {"linked_to": slot_id(ref_type), "ratio": ratio}

    warnings.append(f"Unrecognized count: {tokens}")
    return None


def parse_slot(line, warnings):
    """
    Parse a slot line:
        bed required 1 to 2 fill: against_wall
        chest optional 1 per bed: corner, against_wall
    Returns slot dict or None.
    """
    if ':' not in line:
        warnings.append(f"Slot line missing ':' — skipped: '{line}'")
        return None

    def_part, _, placement_part = line.partition(':')
    tokens = def_part.strip().lower().split()

    # Find required/optional anchor
    req_idx = next(
        (i for i, t in enumerate(tokens) if t in ('required', 'optional')),
        None
    )
    if req_idx is None:
        warnings.append(f"Missing 'required'/'optional' in: '{line}'")
        return None

    required     = tokens[req_idx] == 'required'
    type_tokens  = tokens[:req_idx]
    rest_tokens  = tokens[req_idx + 1:]

    # Optional 'overlap' modifier immediately after required/optional
    allow_overlap = False
    if rest_tokens and rest_tokens[0] == 'overlap':
        allow_overlap = True
        rest_tokens = rest_tokens[1:]

    count_tokens = rest_tokens

    if not type_tokens:
        warnings.append(f"Missing type before 'required'/'optional' in: '{line}'")
        return None

    obj_type = '_'.join(type_tokens)   # multi-word → underscore-joined

    count = parse_count(count_tokens, warnings)
    if count is None:
        return None

    placements = [p.strip() for p in placement_part.split(',') if p.strip()]
    if not placements:
        warnings.append(f"No placements found in: '{line}'")

    slot = {
        "id":                   slot_id(obj_type),
        "type":                 obj_type,
        "required":             required,
        "count":                count,
        "placement_preference": placements,
    }
    if allow_overlap:
        slot["allow_overlap"] = True
    return slot


def parse_rtl(source, file_id):
    warnings = []

    lines = []
    for raw in source.splitlines():
        stripped = raw.lstrip()
        if not stripped or stripped.startswith('#'):
            continue
        indent = len(raw) - len(stripped)
        lines.append((indent, raw.rstrip()))

    if not lines:
        return None, ["File is empty"]

    # --- Header: template "name": ---
    _, first = lines[0]
    m = re.search(r'template\b.*?"([^"]+)"', first, re.IGNORECASE)
    if not m:
        return None, [f"Expected: template \"name\":  — got: '{first.strip()}'"]

    display_name = m.group(1)
    template = {
        "id":               file_id,
        "description":      display_name[0].upper() + display_name[1:],
        "ddl_aliases":      [display_name.lower()],
        "min_size":         None,
        "slots":            [],
        "constraints":      [],
        "todo_constraints": [],
    }

    # --- Body ---
    for indent, raw in lines[1:]:
        line = raw.strip()
        lower = line.lower()

        # min_size: WxH
        if lower.startswith('min_size'):
            _, _, value = line.partition(':')
            value = value.strip().replace('×', 'x')
            parts = value.lower().split('x')
            if len(parts) == 2:
                try:
                    template["min_size"] = {"w": int(parts[0]), "h": int(parts[1])}
                except ValueError:
                    warnings.append(f"Invalid min_size value: '{value}'")
            else:
                warnings.append(f"Invalid min_size format: '{value}'")
            continue

        # constraints: <list>
        if lower.startswith('constraints'):
            _, _, rest = line.partition(':')
            template["constraints"] = [x.strip() for x in rest.split(',') if x.strip()]
            continue

        # todo: <list>
        if lower.startswith('todo'):
            _, _, rest = line.partition(':')
            template["todo_constraints"] = [x.strip() for x in rest.split(',') if x.strip()]
            continue

        # slot line (indented)
        if indent > 0:
            slot = parse_slot(line, warnings)
            if slot:
                template["slots"].append(slot)
            continue

        warnings.append(f"Unrecognized line: '{line}'")

    return template, warnings


def main():
    ap = argparse.ArgumentParser(description="Compile core RTL room template → JSON")
    ap.add_argument("input",          help="Path to .rtl file")
    ap.add_argument("-o", "--output", help="Output .json (default: same dir, .json extension)")
    args = ap.parse_args()

    src = Path(args.input)
    if not src.exists():
        print(f"ERROR: not found: {src}", file=sys.stderr)
        sys.exit(1)

    if args.output:
        dst = Path(args.output)
    else:
        BUILD_ROOMS.mkdir(parents=True, exist_ok=True)
        dst = BUILD_ROOMS / (src.stem + ".json")

    template, warnings = parse_rtl(src.read_text(encoding="utf-8"), src.stem)

    for w in warnings:
        print(f"WARNING: {w}", file=sys.stderr)

    if template is None:
        print("ERROR: parse failed", file=sys.stderr)
        sys.exit(1)

    dst.write_text(json.dumps(template, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"✓ {dst}" + (f"  ({len(warnings)} warning(s))" if warnings else ""))


if __name__ == "__main__":
    main()
