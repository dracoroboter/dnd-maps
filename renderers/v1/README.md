# Renderer SVG v1

Renderer che convertono un `dungeon_base.json` (generato da `generator/generate-dungeon.py`) in SVG con stili visivi diversi. Supportano un layer opzionale di enrichment (oggetti, gate, finestre).

## Pipeline

```
dungeon_base.json ──┬──→ json-to-svg-oldschool.py ──→ .svg (stile principale)
                    ├──→ json-to-svg-blueprint.py  ──→ .svg
                    ├──→ json-to-svg-stone.py      ──→ .svg
                    ├──→ json-to-svg-kenney.py     ──→ .svg (tileset esterno)
                    ├──→ json-to-svg-iso.py        ──→ .svg (isometrico, prototipo)
                    ├──→ json-to-svg.py            ──→ .svg (tileset DCSS, legacy)
                    └──→ json-to-tmx.py            ──→ .tmx (Tiled Map Editor)

(opzionale)
dungeon_enrichment.json ──→ --enrichment flag ──→ oggetti + gate nel SVG
```

## Renderer disponibili

| Script | Stile | Enrichment | Note |
|--------|-------|------------|------|
| `json-to-svg-oldschool.py` | B&W, hatching muri, griglia pavimento | ✅ oggetti + gate | **Stile principale** |
| `json-to-svg-blueprint.py` | Linee blu su sfondo crema, griglia millimetrata | ❌ | |
| `json-to-svg-stone.py` | Texture pietra procedurale (Pillow) | ❌ | |
| `json-to-svg-kenney.py` | Tileset Kenney Scribble Dungeons | ❌ | Sperimentale, richiede tileset esterno |
| `json-to-svg-iso.py` | Isometrico 2:1, muri con altezza | ✅ oggetti | Prototipo |
| `json-to-svg.py` | Tileset DCSS (Dungeon Crawl Stone Soup) | ❌ | Legacy |
| `json-to-tmx.py` | Export Tiled Map Editor | ❌ | Non è un renderer SVG |

## Uso

Tutti i renderer condividono la stessa interfaccia base:

```bash
# Rendering base
python3 renderers/v1/json-to-svg-oldschool.py dungeon_base.json --output mappa.svg

# Con enrichment (solo oldschool e iso)
python3 renderers/v1/json-to-svg-oldschool.py dungeon_base.json \
  --enrichment dungeon_enrichment.json \
  --output mappa.svg

# Vista giocatori (nasconde porte segrete e note DM)
python3 renderers/v1/json-to-svg-oldschool.py dungeon_base.json \
  --enrichment dungeon_enrichment.json \
  --view players \
  --output mappa_players.svg
```

### Parametri comuni

| Parametro | Default | Descrizione |
|-----------|---------|-------------|
| `input` | (obbligatorio) | Path al `dungeon_base.json` |
| `--output` | `<input>_<stile>.svg` | File SVG output |
| `--tile-size` | 24 | Dimensione tile in pixel |
| `--seed` | random | Seed per elementi random (hatching, texture) |
| `--enrichment` | — | Path al `dungeon_enrichment.json` (solo oldschool, iso) |
| `--view` | `dm` | `dm` o `players` (solo oldschool, iso) |

### Parametri specifici

| Renderer | Parametro | Default | Descrizione |
|----------|-----------|---------|-------------|
| `json-to-svg-kenney.py` | `--tileset` | `goodExamples/kenney_scribble-dungeons/...` | Directory tileset PNG |
| `json-to-svg.py` | `--tileset` | `assets/tilesets/dcss` | Directory tileset DCSS |
| `json-to-tmx.py` | `--tileset` | `assets/tilesets/dcss` | Directory tileset per TMX |

## Modulo condiviso: dungeon_svg_core.py

Libreria usata da tutti i renderer. Carica il JSON, ricostruisce la griglia 2D, espone utility.

### Funzioni

| Funzione | Descrizione |
|----------|-------------|
| `load_data(path)` | Carica e restituisce il JSON dungeon |
| `rebuild_grid(rooms, gw, gh)` | Ricostruisce griglia 2D `[y][x]` da lista rooms |
| `get_grid_size(data)` | Restituisce `(gw, gh)` da `data['grid_size']` |
| `get_passages(data)` | Restituisce `{(x,y): orient}` dai passages |
| `bounding_box(grid, gw, gh, margin)` | Bounding box del dungeon (min/max coordinate) |
| `is_exterior_wall(grid, x, y, gh, gw)` | `True` se la cella è muro sul perimetro esterno |
| `write_svg(path, lines)` | Scrive lista di stringhe SVG su file |

### Costanti griglia

```python
WALL = 0    # muro
FLOOR = 1   # pavimento stanza
CORR = 2    # corridoio
EXTERIOR = 3  # esterno (fuori dal dungeon)
```

## Sistema plugin

### Oggetti

Ogni tipo di oggetto ha due file in `templates/objects/`:
- `<tipo>.json` — definizione (dimensioni, proprietà, descrizione)
- `<tipo>_oldschool.py` — renderer per lo stile oldschool

Il renderer oldschool carica i plugin dinamicamente per tipo. L'interfaccia:

```python
def render(obj, tpl, ox, oy, ow, oh, tile, L):
    # obj: dict dall'enrichment (type, x, y, direction, ...)
    # tpl: dict dal template JSON
    # ox, oy: pixel top-left
    # ow, oh: pixel width/height
    # tile: dimensione tile in pixel
    # L: lista SVG a cui appendere
```

Oggetti disponibili: `altar`, `bed`, `bookshelf`, `candelabra`, `chair`, `chest`, `coin_pile`, `column`, `demonic_pentacle`, `fountain`, `large_fountain`, `large_table`, `mask`, `reading_table`, `robe`, `stained_glass`, `table`, `tapestry`, `throne_platform`, `weapon_rack`.

### Gate

Un unico plugin `templates/gates/gate_oldschool.py` gestisce tutti i tipi di gate. Definizioni in `templates/gates/<tipo>.json`.

```python
def render_gate(gate, orient, px, py, pw, ph, tile, sw, L):
    # gate: dict dall'enrichment (type, state)
    # orient: 'h' | 'v'
    # px, py: pixel top-left del passage
    # pw, ph: pixel width/height
    # tile, sw: dimensione tile e stroke-width
    # L: lista SVG
```

Tipi: `door` (open/closed/locked), `portcullis` (open/closed), `arch` (open), `secret` (hidden/found).

## Formato JSON di input

Documentazione completa in `docs/MapsPipelineDocs.md`, sezione "Formato JSON".

### dungeon_base.json (struttura minima)

```json
{
  "seed": 42,
  "title": "Nome Dungeon",
  "grid_size": "60x60",
  "rooms": [
    {"id": "S1", "type": "room", "x": 5, "y": 5, "w": 8, "h": 6}
  ],
  "corridors": [
    {"id": "C1", "type": "corridor", "x": 13, "y": 7, "w": 4, "h": 2}
  ],
  "passages": [
    {"x": 13, "y": 7, "orient": "v", "width": 2}
  ]
}
```

### dungeon_enrichment.json (struttura minima)

```json
{
  "base": "dungeon_base.json",
  "gates": [
    {"x": 13, "y": 7, "type": "door", "state": "locked"}
  ],
  "objects": [
    {"room": "S1", "type": "chest", "x": 1, "y": 1}
  ]
}
```

## Dipendenze

- **Python 3.8+**
- **Pillow** — solo per `json-to-svg-stone.py` (texture procedurali)
- **Tileset Kenney** — esterno, per `json-to-svg-kenney.py`
- **Tileset DCSS** — in `assets/tilesets/dcss/`, per `json-to-svg.py` e `json-to-tmx.py`
