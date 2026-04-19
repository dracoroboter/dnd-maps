# dnd-maps

Toolchain per generare, descrivere e renderizzare mappe per D&D 5e.
Estratto da [dnd-generator](https://github.com/dracoroboter/dnd-generator) come progetto indipendente.

**Stato**: progetto aperto, in sviluppo attivo.

---

## Cosa fa

Tre pipeline parallele per creare mappe dungeon, fogne, taverne, edifici:

### Pipeline v1 — Generazione procedurale

```
generate-dungeon.py  →  dungeon_base.json + .png
                              │
                              ▼
                     json-to-svg-*.py  →  .svg (6 stili)
```

Genera dungeon casuali con algoritmo cell-grid, poi li renderizza in SVG con stili diversi (oldschool, blueprint, kenney, isometrico, pietra, tileset).

### Pipeline DDL/RTL — Arredamento dungeon

```
template .rtl  →  rtl-to-json.py  →  room_template.json
                                            │
testo .ddl  →  ddl-to-enrichment.py  →  enrichment.json  →  SVG arricchito
```

Sistema a due livelli per descrivere l'arredamento delle stanze senza coordinate manuali. RTL definisce archetipi di stanza, DDL descrive un dungeon specifico.

### Pipeline v2 — Mappe scritte a mano

```
mappa.json (v2)  →  json2-to-svg.py  →  .svg
```

Formato JSON compatto per mappe di interni (fogne, taverne, dungeon) disegnate a mano. Renderer SVG in stile "penna su carta".

### Script esterni (Watabou)

Automazione browser (Playwright) per generare mappe da [Watabou](https://watabou.itch.io/): dungeon, città, regioni.

---

## Struttura del repository

```
dnd-maps/
├── generator/              # generazione procedurale dungeon
│   ├── generate-dungeon.py
│   └── archive/            # versioni precedenti (riferimento)
│
├── renderers/
│   ├── v1/                 # renderer SVG da dungeon_base.json
│   │   ├── dungeon_svg_core.py    # modulo condiviso
│   │   ├── json-to-svg-oldschool.py
│   │   ├── json-to-svg-blueprint.py
│   │   ├── json-to-svg-kenney.py
│   │   ├── json-to-svg-iso.py
│   │   ├── json-to-svg-stone.py
│   │   ├── json-to-svg.py         # legacy (tileset)
│   │   └── json-to-tmx.py         # export Tiled
│   └── v2/                 # renderer SVG da JSON v2
│       └── json2-to-svg.py
│
├── ddl-rtl/                # pipeline arredamento dungeon
│   ├── rtl-to-json.py
│   ├── template-apply.py
│   ├── ddl-to-enrichment.py
│   └── enrichment-to-description.py
│
├── external-scripts/       # automazione Watabou (Node.js/Playwright)
│
├── templates/              # definizioni oggetti, stanze, gate
│   ├── objects/            # 20 tipi (JSON + renderer oldschool)
│   ├── rooms/              # 7 archetipi stanza (.rtl)
│   └── gates/              # 4 tipi porta (JSON + renderer oldschool)
│
├── assets/                 # risorse grafiche
│   └── tilesets/dcss/
│
├── tests/                  # script di test
├── examples/v2/            # mappe JSON v2 di esempio
│
├── docs/                   # documentazione completa
│   ├── PlanMaps.md                    # piano master
│   ├── MapsPipelineDocs.md            # doc tecnica pipeline v1
│   ├── DungeonIterationWorkflow.md    # processo iterativo
│   ├── Maps.md                        # doc script Watabou
│   ├── ddl/                           # specifiche DDL/RTL
│   └── v2/                            # doc pipeline v2
│
└── build/                  # output compilati (gitignored)
    └── rooms/
```

---

## Indice documentazione

```
docs/
├── PlanMaps.md ◄──────────────── piano master, fonte di verità pipeline v1
│   ├── MapsPipelineDocs.md        documentazione tecnica dettagliata
│   │   └► renderers/v1/README.md  riferimento operativo per i renderer
│   └── DungeonIterationWorkflow.md  processo iterativo AI+DM
│
├── ddl/
│   ├── PlanIntermediateRepresentation.md ◄── fonte di verità DDL/RTL
│   │   ├── DDL-spec.md                       specifica sintattica DDL v0.3
│   │   └── RTL-spec.md                       specifica sintattica RTL v0.1
│   │
│   (DDL/RTL producono enrichment.json consumato dai renderer v1)
│
├── v2/
│   ├── PlanDungeonV2.md ◄──────── fonte di verità pipeline v2
│   │   └── README.md               doc operativa json2-to-svg.py
│   └── ReverseEngineeringOldschool.md  analisi codice v1 per riuso in v2
│
├── Maps.md                         doc script Watabou (external-scripts/)
│
└── ideas/
    ├── LineaA-CheatSheetDM.md      formato .mapsheet → schede DM per tavolo
    └── LineaB-MappeOnline.md       pipeline mappe Roll20 (asset-renderer)
```

### Relazioni tra documenti

| Documento | Tipo | Dipende da | Alimenta |
|-----------|------|------------|----------|
| `PlanMaps.md` | Piano | — | MapsPipelineDocs, DungeonIterationWorkflow |
| `MapsPipelineDocs.md` | Doc tecnica | PlanMaps | renderers/v1/README |
| `renderers/v1/README.md` | Doc operativa | MapsPipelineDocs | — |
| `DungeonIterationWorkflow.md` | Processo | PlanMaps | — |
| `PlanIntermediateRepresentation.md` | Piano | PlanMaps | DDL-spec, RTL-spec |
| `DDL-spec.md` | Specifica | PlanIntermediateRepresentation | ddl-to-enrichment.py |
| `RTL-spec.md` | Specifica | PlanIntermediateRepresentation | rtl-to-json.py |
| `PlanDungeonV2.md` | Piano | PlanMaps (tecniche riusabili) | v2/README |
| `v2/README.md` | Doc operativa | PlanDungeonV2 | — |
| `ReverseEngineeringOldschool.md` | Analisi | MapsPipelineDocs (codice v1) | PlanDungeonV2 (porting) |
| `Maps.md` | Doc operativa | — | — |
| `LineaA-CheatSheetDM.md` | Idea | — | (futuro: mapsheet-to-dm.py) |
| `LineaB-MappeOnline.md` | Idea | — | (futuro: asset-renderer.py) |

### Relazioni documenti ↔ codice

| Documento | Script governati | Dati consumati/prodotti |
|-----------|-----------------|------------------------|
| `PlanMaps.md` | `generator/generate-dungeon.py` | → `dungeon_base.json` + `.png` + `.md` |
| `MapsPipelineDocs.md` | `renderers/v1/*`, `tests/*` | ← `dungeon_base.json`, ← `dungeon_enrichment.json` |
| `DDL-spec.md` | `ddl-rtl/ddl-to-enrichment.py` | ← `.ddl` → `dungeon_enrichment.json` |
| `RTL-spec.md` | `ddl-rtl/rtl-to-json.py` | ← `.rtl` → `build/rooms/*.json` |
| `PlanIntermediateRepresentation.md` | `ddl-rtl/template-apply.py`, `ddl-rtl/enrichment-to-description.py` | ← `templates/objects/*.json`, `build/rooms/*.json` |
| `PlanDungeonV2.md` / `v2/README.md` | `renderers/v2/json2-to-svg.py` | ← JSON v2 → `.svg` |
| `Maps.md` | `external-scripts/generate-watabou-*.js` | → mappe PNG/SVG |

---

## Uso rapido

### Generare un dungeon e renderizzarlo

```bash
# Genera dungeon
python generator/generate-dungeon.py --seed 42 --rooms 10 --output dungeon

# Renderizza in SVG oldschool
python renderers/v1/json-to-svg-oldschool.py dungeon_base.json --output dungeon.svg
```

### Arredare un dungeon con DDL

```bash
# Compilare un template stanza
python ddl-rtl/rtl-to-json.py templates/rooms/chapel.rtl

# Compilare un file DDL
python ddl-rtl/ddl-to-enrichment.py avventura.ddl --dungeon dungeon_base.json --output enrichment.json

# Renderizzare con arredamento
python renderers/v1/json-to-svg-oldschool.py dungeon_base.json --enrichment enrichment.json --output dungeon.svg
```

### Renderizzare una mappa v2

```bash
python renderers/v2/json2-to-svg.py examples/v2/fogna_oakshore.json --output fogna.svg
```

---

## Roadmap

### Linea A — Cheat sheet per sessioni dal vivo

Formato sorgente leggero per descrivere mappe + script che genera schede DM (layout ASCII, misure in quadretti, posizioni nemici/trappole) per disegnare al tavolo.

### Linea B — Mappe per sessioni online (Roll20)

Pipeline per produrre mappe con qualità grafica accettabile per VTT. Opzioni in valutazione:
- Miglioramento renderer esistenti (tileset, texture, ombre)
- Export in formato compatibile Roll20
- Pipeline ibrida sorgente proprio → rendering esterno

### TODO aperti

- [x] ~~Documentazione dedicata per i renderer v1~~ → `renderers/v1/README.md`
- [ ] Compilare 3 template RTL mancanti (guard_room, library, throne_room)
- [ ] Rimuovere 3 asset DCSS orfani (floor_crystal, wall_brick, wall_stone)
- [ ] Fix json-to-tmx.py: usa dungeon_svg_core invece di ridefinire rebuild_grid()

---

## Dipendenze

- **Python 3.8+**
- **Pillow** — per `generate-dungeon.py` e `json-to-svg-stone.py`
- **Node.js + Playwright** — solo per script Watabou in `external-scripts/`

---

## Licenza

| contenuto | licenza |
|-----------|---------|
| Script e software | [GNU General Public License v2 (GPLv2)](https://www.gnu.org/licenses/old-licenses/gpl-2.0.html) |
| Documentazione | [Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)](https://creativecommons.org/licenses/by-sa/4.0/) |

## Autore

**dracoroboter** — `dracoroboter(at)gmail.com`
