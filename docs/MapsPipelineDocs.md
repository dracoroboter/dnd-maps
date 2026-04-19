# Documentazione Tecnica — Pipeline Mappe Dungeon

> Ultimo aggiornamento: 2026-04-13 (sessione 2)

---

## Indice

1. [Pipeline generale](#pipeline-generale)
2. [Script attivi](#script-attivi)
3. [Modulo comune](#modulo-comune)
4. [Template oggetti](#template-oggetti)
5. [Template gate](#template-gate)
6. [Script di test](#script-di-test)
7. [Script archiviati](#script-archiviati)
8. [Formato JSON](#formato-json)
9. [Convenzioni](#convenzioni)

---

## Pipeline generale

```
generate-dungeon.py
        │
        ▼
dungeon_base.json + dungeon_base.png
        │
        ▼  (editato manualmente o via wizard)
dungeon_enrichment.json
        │
        ▼  (passato con --enrichment al renderer)
json-to-svg-oldschool.py  ←── stile principale
json-to-svg-blueprint.py
json-to-svg-stone.py
json-to-svg-kenney.py
json-to-svg.py            ←── tileset DCSS
        │
        ▼
dungeon_base_oldschool.svg  (+ altri stili)
```

**Nota:** il merge base+enrichment avviene al volo nel renderer (`--enrichment` + `--view dm|players`). Non esistono file separati DM/players su disco.

---

## Script attivi

### `generate-dungeon.py`

**Funzione:** Generatore principale del dungeon. Algoritmo cell-grid con BFS/MST.

**Input:** parametri CLI  
**Output:** `dungeon_base.json`, `dungeon_base.png`, `dungeon_base.md`

**Uso:**
```bash
python3 tech/scripts/generate-dungeon.py \
  --seed 42 --rooms 12 --title "Nome Dungeon" \
  --corridor-rows 3 --output tech/reports/dungeon_base.png
```

**Parametri principali:**

| Parametro | Default | Descrizione |
|-----------|---------|-------------|
| `--seed` | random | Seed per riproducibilità |
| `--rooms` | 8 | Numero target di stanze |
| `--title` | "Dungeon" | Titolo del dungeon |
| `--corridor-rows` | 2 | Righe di corridoi nella griglia |
| `--output` | `dungeon_base.png` | File PNG output (il JSON ha stesso nome) |

**Struttura JSON output:** vedi sezione [Formato JSON](#formato-json).

---

### `json-to-svg-oldschool.py`

**Funzione:** Renderer principale. Stile old-school D&D: B&W, hatching random sui muri, griglia pavimento, gate con plugin.

**Input:** `dungeon_base.json` + (opzionale) `dungeon_enrichment.json`  
**Output:** SVG

**Uso:**
```bash
python3 tech/scripts/json-to-svg-oldschool.py \
  tech/reports/dungeon_base.json \
  --enrichment tech/reports/dungeon_enrichment.json \
  --tile-size 24 --output tech/reports/dungeon_base_oldschool.svg
```

**Funzionalità:**
- Hatching random sui muri (linee ~45°, densità variabile)
- Griglia grigio chiaro sul pavimento
- Bordi neri tra pavimento e muro
- Passage con gate (plugin `gate_oldschool.py`)
- Finestre (trattino tratteggiato sul muro esterno)
- Oggetti da enrichment (plugin `tipo_oldschool.py`)
- Etichette stanze

**Dipendenze:** `dungeon_svg_core.py`, `tech/templates/gates/gate_oldschool.py`, plugin oggetti

---

### `json-to-svg-blueprint.py`

**Funzione:** Renderer stile schizzo su carta millimetrata. Linee blu su sfondo bianco/crema, griglia millimetrata.

**Input:** `dungeon_base.json`  
**Output:** SVG

**Uso:**
```bash
python3 tech/scripts/json-to-svg-blueprint.py \
  tech/reports/dungeon_base.json \
  --tile-size 24 --output tech/reports/dungeon_base_blueprint.svg
```

**Dipendenze:** `dungeon_svg_core.py`

---

### `json-to-svg-stone.py`

**Funzione:** Renderer stile texture pietra procedurale. Muri con pattern pietra, pavimento con texture.

**Input:** `dungeon_base.json`  
**Output:** SVG

**Uso:**
```bash
python3 tech/scripts/json-to-svg-stone.py \
  tech/reports/dungeon_base.json \
  --tile-size 24 --output tech/reports/dungeon_base_stone.svg
```

**Dipendenze:** `dungeon_svg_core.py`

---

### `json-to-svg-kenney.py`

**Funzione:** Renderer stile Kenney Scribble Dungeons. Usa tileset PNG (64px) da `goodExamples/kenney_scribble-dungeons/`.

**Input:** `dungeon_base.json` + tileset PNG  
**Output:** SVG con immagini base64 embedded

**Uso:**
```bash
python3 tech/scripts/json-to-svg-kenney.py \
  tech/reports/dungeon_base.json \
  --tile-size 32 --output tech/reports/dungeon_base_kenney.svg
```

**Note:** Sperimentale. Angoli corridoio da sistemare.

**Dipendenze:** `dungeon_svg_core.py`, tileset Kenney PNG

---

### `json-to-svg.py`

**Funzione:** Renderer tileset DCSS (Dungeon Crawl Stone Soup). Usa tileset PNG da `tech/assets/tilesets/dcss/`.

**Input:** `dungeon_base.json` + tileset PNG  
**Output:** SVG con immagini base64 embedded

**Uso:**
```bash
python3 tech/scripts/json-to-svg.py \
  tech/reports/dungeon_base.json \
  --tile-size 24 --output tech/reports/dungeon_base.svg
```

**Dipendenze:** `dungeon_svg_core.py`, tileset DCSS PNG

---

### `json-to-tmx.py`

**Funzione:** Export in formato TMX per Tiled Map Editor.

**Input:** `dungeon_base.json`  
**Output:** `.tmx`

**Uso:**
```bash
python3 tech/scripts/json-to-tmx.py \
  tech/reports/dungeon_base.json \
  --output tech/reports/dungeon_base.tmx
```

---

### `json-to-svg-iso.py` *(esperimento)*

**Funzione:** Renderer isometrico prototipo. Proiezione 2:1, muri con altezza configurabile, porte come ante, oggetti flat sul pavimento.

**Input:** `dungeon_base.json` + (opzionale) `dungeon_enrichment.json`  
**Output:** SVG

**Uso:**
```bash
python3 tech/scripts/json-to-svg-iso.py \
  tech/reports/dungeon_base.json \
  --enrichment tech/reports/dungeon_enrichment.json \
  --tile-size 24 --output tech/reports/dungeon_base_iso.svg
```

**Stato:** prototipo funzionante, non prioritario.

---

## Modulo comune

### `dungeon_svg_core.py`

**Funzione:** Libreria condivisa da tutti i renderer SVG.

**Funzioni esportate:**

| Funzione | Descrizione |
|----------|-------------|
| `load_data(path)` | Carica JSON dungeon |
| `rebuild_grid(rooms, gw, gh)` | Ricostruisce griglia 2D da rooms |
| `get_grid_size(data)` | Restituisce `(gw, gh)` da `data['grid_size']` |
| `get_passages(data)` | Restituisce `{(x,y): orient}` da `data['passages']` |
| `bounding_box(grid, gw, gh, margin)` | Calcola bounding box del dungeon |
| `is_exterior_wall(grid, x, y, gh, gw)` | True se il muro è sul perimetro esterno |
| `write_svg(path, lines)` | Scrive lista di stringhe SVG su file |

**Costanti:**

```python
WALL = 0, FLOOR = 1, CORR = 2, EXTERIOR = 3
```

---

## Template oggetti

Percorso: `tech/templates/objects/`

Ogni oggetto ha:
- `tipo.json` — definizione (size, directional, properties, description)
- `tipo_oldschool.py` — plugin renderer per stile OLDSCHOOL

### Interfaccia plugin oggetto

```python
def render(obj, tpl, ox, oy, ow, oh, tile, L):
    """
    obj  : dict dall'enrichment (type, x, y, direction, proprietà extra)
    tpl  : dict dal template JSON
    ox,oy: pixel top-left dell'oggetto
    ow,oh: pixel width/height dell'oggetto
    tile : dimensione tile in pixel
    L    : lista SVG a cui appendere elementi
    """
```

### Oggetti disponibili

| Tipo | Size | Direzionale | Proprietà extra | Descrizione |
|------|------|-------------|-----------------|-------------|
| `chest` | 1×1 | no | — | Forziere |
| `column` | 1×1 | no | — | Colonna |
| `altar` | 2×1 | no | — | Altare |
| `bed` | 1×2 | sì | `sheet_type: plain\|dots` | Letto |
| `bookshelf` | 1×2 | sì | — | Libreria |
| `table` | 2×1 | no | — | Tavolo |
| `large_table` | 2×4 | no | — | Tavolo grande |
| `fountain` | 2×2 | no | — | Fontana |
| `large_fountain` | 4×4 | no | — | Fontana grande |
| `demonic_pentacle` | 5×5 | no | — | Pentacolo demoniaco |

**Coordinate oggetti nell'enrichment:** `x` e `y` sono interi in quadretti relativi all'angolo top-left della stanza.

**`allow_overlap`:** se `true`, l'oggetto viene disegnato sopra gli altri (es. altare sul pentacolo) e non occupa spazio nel check sovrapposizione. Gli oggetti con `allow_overlap: false` (default) vengono renderizzati prima; quelli con `allow_overlap: true` dopo (in primo piano).

---

## Template gate

Percorso: `tech/templates/gates/`

Ogni tipo di gate ha:
- `tipo.json` — stati validi, stato default, descrizione
- `gate_oldschool.py` — plugin renderer unico per tutti i tipi (stile OLDSCHOOL)

### Interfaccia plugin gate

```python
def render_gate(gate, orient, px, py, pw, ph, tile, sw, L):
    """
    gate        : dict dall'enrichment (type, state, x, y)
    orient      : 'h' | 'v'  (dal passage corrispondente)
    px,py       : pixel top-left del passage
    pw,ph       : pixel width/height del passage
    tile        : dimensione tile in pixel
    sw          : stroke-width base
    L           : lista SVG
    """
```

### Gate disponibili

| Tipo | Stati | Default | Descrizione |
|------|-------|---------|-------------|
| `door` | open, closed, locked | closed | Porta |
| `portcullis` | open, closed | closed | Saracinesca |
| `arch` | open | open | Arco |
| `secret` | hidden, found | hidden | Porta segreta |

**Passage senza gate in enrichment:** renderizzato come `door closed` di default.  
**Porta segreta `hidden`:** il passage non viene disegnato (rimane muro).

---

## Script di test

| Script | Output | Descrizione |
|--------|--------|-------------|
| `test-object-bed.py` | `object_test_bed.svg` | Test visivo letto (4 direzioni × 2 sheet_type) |
| `test-object-table.py` | `object_test_table.svg` | Test visivo tavolo e tavolo grande |
| `test-object-pentacle.py` | `object_test_pentacle.svg` | Test visivo pentacolo demoniaco |

---

## Script archiviati

Script storici conservati per riferimento, non più in uso attivo:

| Script | Versione | Note |
|--------|----------|------|
| `generate-dungeon-bsp-0.1.py` | 0.1 | Algoritmo BSP, abbandonato |
| `generate-dungeon-cell-grid-0.2.py` | 0.2 | Cell-grid senza corridoi unificati |
| `generate-dungeon-cell-grid-0.3.py` | 0.3 | Versione stabile pre-refactoring |
| `json-to-svg-0.1.py` | 0.1 | Renderer DCSS originale |
| `json-to-svg-oldschool-0.1.py` | 0.1 | OLDSCHOOL prima versione |
| `json-to-svg-oldschool-0.2.py` | 0.2 | OLDSCHOOL con porte |
| `json-to-svg-oldschool-0.3.py` | 0.3 | OLDSCHOOL stabile pre-enrichment |
| `json-to-svg-kenney-0.1.py` | 0.1 | Kenney prima versione |
| `json-to-svg-stone-0.1.py` | 0.1 | Stone prima versione |
| `json-to-svg-blueprint-0.1.py` | 0.1 | Blueprint prima versione |

---

## Formato JSON

### `dungeon_base.json`

```json
{
  "seed": 42,
  "title": "Nome Dungeon",
  "generated": "2026-04-13",
  "grid_size": "60x60",
  "rooms": [
    {"id": "S1", "type": "room", "x": 5, "y": 5, "w": 8, "h": 6}
  ],
  "corridors": [
    {"id": "C1", "type": "corridor", "x": 13, "y": 7, "w": 4, "h": 2}
  ],
  "passages": [
    {"x": 13, "y": 7, "orient": "v", "width": 2},
    {"x": 23, "y": 48, "orient": "h", "width": 1, "external": true}
  ]
}
```

**Costanti griglia:** `WALL=0, FLOOR=1, CORR=2, EXTERIOR=3`  
**Orientamento passage:** `orient='h'` = muro orizzontale (celle consecutive su asse x); `orient='v'` = muro verticale (celle consecutive su asse y)  
**`width`:** numero di celle consecutive che formano il passage (calcolato dal generatore)  
**1 quadretto = 5ft = 1,5m** (standard D&D 5e)

### `dungeon_enrichment.json`

```json
{
  "base": "dungeon_base.json",
  "gates": [
    {"x": 13, "y": 7,  "type": "door",       "state": "locked"},
    {"x": 20, "y": 15, "type": "portcullis",  "state": "closed"},
    {"x": 30, "y": 22, "type": "arch",        "state": "open"},
    {"x": 40, "y": 30, "type": "secret",      "state": "hidden"}
  ],
  "windows": [
    {"room": "S5", "wall": "right"}
  ],
  "objects": [
    {"room": "S1", "type": "chest",            "x": 1, "y": 1},
    {"room": "S4", "type": "bed",              "x": 2, "y": 1, "direction": "south", "sheet_type": "dots"},
    {"room": "S7", "type": "demonic_pentacle", "x": 1, "y": 1},
    {"room": "S7", "type": "altar",            "x": 2, "y": 2, "allow_overlap": true}
  ]
}
```

---

## Convenzioni

- **Nomi tecnici in inglese:** `bed`, `door`, `passage`, `gate`, `locked`
- **Descrizioni in italiano:** `"description": "Letto"`, `"description": "Porta"`
- **Lingua nel codice:** script Python (codice + commenti) in inglese; chiavi JSON in inglese; campo `description` in italiano; file `.ddl` in italiano (è il linguaggio semi-naturale per definizione); documentazione `.md` in italiano
- **Backup:** escludono sempre `goodExamples/` e `legacy/`
- **Copyright:** `© Dracosoft CC BY`
- **Nomi file output:** `dungeon_base.*` (non `dungeon_latest.*`)
- **Plugin renderer:** un file per tipo oggetto (`tipo_oldschool.py`), un file per tutti i gate (`gate_oldschool.py`)

---

## Linee di sviluppo future

- **DSL intermedio** — linguaggio semi-naturale per creare enrichment senza scrivere JSON a mano. Vedi `tech/rules/PlanIntermediateRepresentation.md`
- **Skill Kiro** — interpreta linguaggio naturale → produce DSL → parser genera JSON
- **Template stanze** — `tech/templates/rooms/` con arredamenti predefiniti per tipo (bedroom, chapel, treasury...)
