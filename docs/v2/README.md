# json2-to-svg.py — Renderer SVG per mappe JSON v2

Renderer SVG in stile "penna su carta" per il formato JSON v2.
A differenza della pipeline v1 (generazione procedurale + enrichment), il JSON v2 è scritto a mano e descrive mappe di interni: fogne, taverne, dungeon, caverne.

**Piano di sviluppo:** `tech/rules/PlanDungeonV2.md`

---

## Uso

```bash
python3 tech/dungeon-v2/json2-to-svg.py <file.json> [-o output.svg] [--view dm|players] [--seed N]
```

| Opzione | Default | Descrizione |
|---------|---------|-------------|
| `-o` | `<input>.svg` | File SVG di output |
| `--view` | `dm` | Vista: `dm` (tutto) o `players` (senza segreti/trappole) |
| `--seed` | `42` | Seed per riproducibilità della tassellatura |

**Dipendenze:** solo libreria standard Python 3 (`json`, `math`, `random`).

---

## Formato JSON v2

```json
{
  "meta": { "name": "...", "author": "...", "date": "...", "license": "...", "grid": 1, "unit": "sq" },
  "areas": [ ... ],
  "connections": [ ... ],
  "objects": [ ... ]
}
```

### Meta

| Campo | Tipo | Descrizione |
|-------|------|-------------|
| `name` | string | Titolo della mappa (centrato nell'header SVG) |
| `author` | string | Autore (nel footer) |
| `date` | string | Data (nel footer) |
| `license` | string | Licenza (nel footer) |
| `grid` | int | Dimensione griglia in unità (default 1) |
| `unit` | string | Unità di misura: `"sq"` (quadretti), `"ft"` (feet) |

### Areas

Ogni area è uno spazio percorribile. Coordinate in quadretti.

| Shape | Parametri | Uso |
|-------|-----------|-----|
| `rect` | `x`, `y`, `w`, `h` | Stanze, corridoi dritti |
| `circle` | `cx`, `cy`, `r` | Cisterne, torri |
| `poly` | `points` (lista `[x,y]`) | Forme irregolari |

Campi comuni:

| Campo | Tipo | Descrizione |
|-------|------|-------------|
| `id` | string | Identificatore univoco (usato nelle connessioni e come label) |
| `label` | string | Nome descrittivo (non renderizzato, solo documentazione) |
| `tags` | list | Tag semantici: `room`, `tunnel`, `boss`, `secret`, `dead_end`, ecc. |
| `style` | string | Stile visivo: `brick`, `stone`, `wood` (futuro: seleziona pattern tassellatura) |

### Connections

Collegano due aree. Il renderer calcola automaticamente i punti di contatto sui bordi.

| Campo | Tipo | Descrizione |
|-------|------|-------------|
| `from` | string | ID area di partenza |
| `to` | string | ID area di arrivo (opzionale per uscite esterne) |
| `type` | string | Tipo di connessione (vedi tabella sotto) |
| `width` | number | Larghezza in quadretti (default 1, solo per `tunnel`/`arch`) |
| `side` | string | Lato di uscita se `to` è assente: `north`/`south`/`east`/`west` |

#### Tipi di connessione

| Tipo | Grafica | Descrizione |
|------|---------|-------------|
| `tunnel` | Varco con bordi laterali | Passaggio aperto — i muri si interrompono |
| `arch` | Come tunnel | Arco decorativo — nessuna separazione funzionale |
| `door` | Varco + linea trasversale + arco | Porta — separazione fisica tra le aree |
| `secret` | Tratteggio rosso + "S" (solo vista DM) | Passaggio segreto — muro intatto in vista players |
| `stairs` | *(da implementare)* | Scale, discese |

**Varco vs porta:** un varco (tunnel/arch) è un'apertura libera nel muro. Una porta (door) ha una separazione grafica (linea trasversale) che indica un elemento fisico.

### Objects

Oggetti posizionati dentro le aree.

| Campo | Tipo | Descrizione |
|-------|------|-------------|
| `area` | string | ID dell'area contenitore |
| `type` | string | Tipo oggetto (vedi sotto) |
| `pos` | `"center"` o `[x, y]` | Posizione (coordinate assolute in quadretti, o `"center"` per il centro dell'area) |
| `hidden` | bool | Se `true`, invisibile in vista `players` |

#### Tipi di oggetto supportati

| Tipo | Grafica |
|------|---------|
| `pillar` | Cerchio grigio pieno |
| `trap` | X rossa |
| `grate` | Quadrato con croce interna |
| `table` / `counter` | Rettangolo vuoto |
| `fireplace` | Rettangolo con linea interna |
| `barrel` | Cerchio vuoto |

---

## Rendering

### Ordine dei layer (dal basso verso l'alto)

1. Background bianco
2. Header (titolo centrato + riga separatrice)
3. Tassellatura intorno alle aree (raggio configurabile)
4. Aree bianche (fill)
5. Griglia quadretti dentro le aree
6. Bordi aree (stroke nero)
7. Connessioni (corridoi, porte) — disegnate sopra i bordi per interromperli (wall-break)
8. Oggetti
9. Label (ID area centrato)
10. Footer (copyright a destra + riga separatrice)

### Tassellatura

Pattern a parquet irregolare (linee incrociate a ±45° con jitter) disegnato nelle celle entro `HATCH_RADIUS` quadretti (default 4) da qualsiasi area. Le celle interne alle aree non vengono tassellate. Le celle oltre il raggio restano bianche (vuoto).

### Wall-break

I corridoi e le porte disegnano una linea bianca spessa nel punto di contatto con il bordo della stanza, interrompendo visivamente il muro. Questo crea l'effetto di un'apertura nel muro.

### Corridoi diagonali

Il renderer supporta corridoi tra aree non allineate. I bordi laterali sono calcolati con vettore perpendicolare alla direzione del corridoio, producendo un parallelogramma.

---

## Costanti configurabili

| Costante | Valore | Descrizione |
|----------|--------|-------------|
| `SQ` | 30 | Pixel per quadretto |
| `MARGIN` | 40 | Margine esterno in pixel |
| `WALL_SW` | 2.0 | Spessore bordo muro |
| `HATCH_RADIUS` | 4 | Raggio tassellatura in quadretti |
| `FONT` | Georgia, serif | Font per label e titolo |

---

## Casi test

| File | Descrizione |
|------|-------------|
| `test/fogna_oakshore.json` | Fogne di FuoriDaHellfire — 11 aree, corridoi lunghi, cisterna circolare, passaggio segreto |
| `test/taverna_franciosibus.json` | Taverna de LAnelloDelConte — 3 stanze, porte, layout compatto |

```bash
# Generare entrambi i test
python3 tech/dungeon-v2/json2-to-svg.py tech/dungeon-v2/test/fogna_oakshore.json --seed 42
python3 tech/dungeon-v2/json2-to-svg.py tech/dungeon-v2/test/taverna_franciosibus.json --seed 42
```

---

## Differenze dalla pipeline v1

| | Pipeline v1 | Pipeline v2 |
|---|---|---|
| **Input** | JSON generato da `generate-dungeon.py` | JSON scritto a mano |
| **Formato** | Griglia di celle (WALL/FLOOR/CORR) | Aree geometriche (rect/circle/poly) |
| **Enrichment** | File separato (`dungeon_enrichment.json`) | Oggetti inline nel JSON |
| **Connessioni** | Derivate dalla griglia (passages) | Esplicite nel JSON |
| **Renderer** | Multipli stili (oldschool, blueprint, stone, kenney, iso) | Singolo stile oldschool |
| **Dipendenze** | `dungeon_svg_core.py` condiviso | Script autonomo |
