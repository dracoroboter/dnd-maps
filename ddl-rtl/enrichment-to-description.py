#!/usr/bin/env python3
"""
enrichment-to-description.py — Genera descrizioni narrative delle stanze da dungeon_enrichment.json.

Per ogni stanza che ha oggetti nell'enrichment, produce un paragrafo in italiano
basato sugli oggetti effettivamente piazzati e sullo stato delle porte.
Aggiorna dungeon_base.md sostituendo le righe "*Descrizione: da completare.*"

Usage:
    python3 ddl-rtl/enrichment-to-description.py \\
        dungeon_enrichment.json \\
        --dungeon dungeon_base.json \\
        --md dungeon_base.md
"""

import json
import re
import argparse
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent
OBJECTS_DIR = SCRIPTS_DIR.parent / "templates" / "objects"

DOOR_STATE_IT = {
    "open":   "aperta",
    "closed": "chiusa",
    "locked": "sbarrata",
    "hidden": "segreta",
}

WALL_IT = {
    "north": "nord",
    "south": "sud",
    "east":  "est",
    "west":  "ovest",
}


def load_obj_tpl(obj_type):
    p = OBJECTS_DIR / f"{obj_type}.json"
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {}


def describe_objects(objects):
    """
    Raggruppa gli oggetti per tipo e produce frasi descrittive.
    Gli oggetti con allow_overlap (sovrapposti) vengono descritti insieme al loro host.
    """
    # Conta per tipo, escludi oggetti sovrapposti (descritti insieme all'host)
    overlap_types = {o["type"] for o in objects if o.get("allow_overlap")}
    counts = {}
    for o in objects:
        if not o.get("allow_overlap"):
            counts[o["type"]] = counts.get(o["type"], 0) + 1

    phrases = []
    for obj_type, n in counts.items():
        tpl = load_obj_tpl(obj_type)
        if n == 1:
            phrase = tpl.get("description_in_room")
        else:
            phrase = tpl.get("description_in_room_plural") or tpl.get("description_in_room")

        if not phrase:
            phrase = tpl.get("description", obj_type)

        # Se questo oggetto ha un sovrapposto (es. altare con pentacolo), aggiungi nota
        if obj_type == "demonic_pentacle" and "altar" in overlap_types:
            phrase += "; al suo centro si trova un altare"

        phrases.append(phrase)

    return phrases


def describe_doors(gates, room_id, dungeon):
    """
    Produce frasi per le porte della stanza.
    Usa le connessioni del dungeon_base per sapere verso dove porta ciascuna porta.
    """
    room = next((r for r in dungeon.get("rooms", []) if r["id"] == room_id), None)
    if not room:
        return []

    # Mappa passage (x,y) → stanza connessa
    passage_to_room = {}
    for r in dungeon.get("rooms", []):
        for conn in r.get("connections", []):
            if conn.get("to") and r["id"] != room_id:
                pass  # costruiamo la mappa dai gate stessi

    # Usiamo le connessioni della stanza corrente
    conn_map = {c["to"]: c for c in room.get("connections", [])}

    # Raggruppa gate per stato
    by_state = {}
    seen_pairs = set()
    for g in gates:
        target = g.get("to") or g.get("target")
        state = g.get("state", "closed")
        key = (target, state)
        if key not in seen_pairs:
            by_state.setdefault(state, set()).add(target or "?")
            seen_pairs.add(key)

    phrases = []
    for state, targets in by_state.items():
        state_it = DOOR_STATE_IT.get(state, state)
        for t in sorted(targets):
            if t and t != "?":
                phrases.append(f"una porta {state_it} conduce a {t}")
            else:
                phrases.append(f"una porta {state_it}")

    return phrases


def build_description(room_id, objects, gates, dungeon):
    """
    Compone il paragrafo descrittivo per una stanza.
    """
    obj_phrases = describe_objects(objects)
    door_phrases = describe_doors(gates, room_id, dungeon)

    all_phrases = obj_phrases + door_phrases
    if not all_phrases:
        return None

    # Capitalizza il primo, unisce con punto e virgola, punto finale
    sentences = []
    for i, p in enumerate(all_phrases):
        if i == 0:
            p = p[0].upper() + p[1:]
        sentences.append(p)

    return "; ".join(sentences) + "."


def update_md(md_path, room_descriptions):
    """
    Aggiorna dungeon_base.md: sostituisce le sezioni "*Descrizione: da completare.*"
    con il testo generato per ogni stanza.
    Lavora sezione per sezione (split su "---") per non attraversare i separatori.
    """
    content = md_path.read_text(encoding="utf-8")

    # Splitta preservando il separatore
    sections = re.split(r'(?m)^---\s*$', content)
    PLACEHOLDER = "*Descrizione: da completare.*"

    for room_id, desc in room_descriptions.items():
        header_re = re.compile(r'^## ' + re.escape(room_id) + r'\b', re.MULTILINE)
        replaced = False
        for i, section in enumerate(sections):
            if header_re.search(section) and PLACEHOLDER in section:
                sections[i] = section.replace(PLACEHOLDER, desc)
                replaced = True
                break
        print(f"  ✓ {room_id}" if replaced else f"  — {room_id}: non trovato o già descritto")

    md_path.write_text("---".join(sections), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description="Genera descrizioni narrative da enrichment JSON")
    ap.add_argument("enrichment", help="Path a dungeon_enrichment.json")
    ap.add_argument("--dungeon",  required=True, help="Path a dungeon_base.json")
    ap.add_argument("--md",       required=True, help="Path a dungeon_base.md da aggiornare")
    args = ap.parse_args()

    enrichment = json.loads(Path(args.enrichment).read_text(encoding="utf-8"))
    dungeon    = json.loads(Path(args.dungeon).read_text(encoding="utf-8"))
    md_path    = Path(args.md)

    # Raggruppa oggetti e gate per stanza
    objs_by_room  = {}
    for o in enrichment.get("objects", []):
        objs_by_room.setdefault(o["room"], []).append(o)

    # Per i gate associa la stanza in base alle connessioni del dungeon
    gates_by_room = {}
    room_coords   = {r["id"]: r for r in dungeon.get("rooms", [])}
    for g in enrichment.get("gates", []):
        gx, gy = g["x"], g["y"]
        for room in dungeon.get("rooms", []):
            rx, ry, rw, rh = room["x"], room["y"], room["w"], room["h"]
            on_border = (
                (gy == ry - 1     and rx <= gx < rx + rw) or
                (gy == ry + rh    and rx <= gx < rx + rw) or
                (gx == rx - 1     and ry <= gy < ry + rh) or
                (gx == rx + rw    and ry <= gy < ry + rh)
            )
            if on_border:
                # Trova la stanza connessa
                for conn in room.get("connections", []):
                    target = conn["to"]
                    if target in room_coords:
                        tr = room_coords[target]
                        trx, try_, trw, trh = tr["x"], tr["y"], tr["w"], tr["h"]
                        on_target = (
                            (gy == try_ - 1     and trx <= gx < trx + trw) or
                            (gy == try_ + trh   and trx <= gx < trx + trw) or
                            (gx == trx - 1      and try_ <= gy < try_ + trh) or
                            (gx == trx + trw    and try_ <= gy < try_ + trh)
                        )
                        if on_target:
                            entry = dict(g, to=target)
                            gates_by_room.setdefault(room["id"], []).append(entry)

    # Genera descrizioni
    all_rooms = set(objs_by_room) | set(gates_by_room)
    room_descriptions = {}
    for room_id in sorted(all_rooms):
        desc = build_description(
            room_id,
            objs_by_room.get(room_id, []),
            gates_by_room.get(room_id, []),
            dungeon
        )
        if desc:
            room_descriptions[room_id] = desc

    print(f"Descrizioni generate per {len(room_descriptions)} stanze:")
    update_md(md_path, room_descriptions)
    print(f"→ {args.md}")


if __name__ == "__main__":
    main()
