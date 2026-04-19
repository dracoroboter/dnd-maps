# Piano: Formato JSON Dungeon v2 + Renderer SVG

## Obiettivo

Un formato JSON compatto per descrivere mappe di interni (fogne, taverne, dungeon, caverne) e un renderer SVG che le disegni in stile "penna su carta".

## Casi test concreti

### A — Fogna (FuoriDaHellfire)
- Corridoi lunghi come struttura principale
- Pochi spazi aperti (cisterna, nido ratti)
- Bivio a 3 vie (2 vicoli ciechi + 1 prosegue)
- Transizione visiva (mattoni → pietra)
- Acqua nei canali
- Percorso quasi lineare

### B — Taverna (LAnelloDelConte, Taberna de Franciosibus)
- Edificio con stanze definite
- Sala grande (taverna), cucina, bagno
- Porta d'ingresso
- Poche connessioni, layout compatto

## Principi del formato

1. **Aree, non celle** — il JSON descrive forme geometriche, non una griglia pixel per pixel
2. **Compatto** — una taverna con 3 stanze = ~20 righe di JSON, non 200
3. **Forme libere** — rettangoli, cerchi, poligoni. Non solo griglie rettangolari.
4. **Connessioni esplicite** — corridoi/porte tra aree sono oggetti di primo livello
5. **Leggibile** — un umano deve poter capire e modificare il JSON a mano
6. **Estensibile** — nuovi tipi di area, connessione, oggetto senza rompere il formato

---

## Definizioni (da PlanMaps v1)

### Elementi strutturali

| Elemento | Descrizione | Rendering |
|----------|-------------|-----------|
| **Vuoto** | Spazio fuori dalla mappa, non esiste nel mondo di gioco | Colore di background (bianco), nessun fill |
| **Muro** | Separa aree tra loro o aree dal vuoto | Bordo nero (stroke), tassellatura esterna |
| **Area** | Spazio interno percorribile (stanza, corridoio, tunnel, sala) | Fill bianco, griglia quadretti |
| **Terra/roccia** | Spazio solido intorno alle aree — non percorribile, non vuoto | Tassellatura (parquet, tratteggio, pattern) |

### Connessioni tra aree

| Tipo | Grafica | Descrizione |
|------|---------|-------------|
| **Varco** (tunnel/arch) | Apertura nel muro, nessuna separazione | Passaggio libero — i muri della stanza si interrompono |
| **Porta** (door) | Apertura + linea trasversale + arco | Separazione fisica tra le aree — indica una porta chiusa/aperta |
| **Segreto** (secret) | Invisibile in vista players, tratteggio rosso in vista DM | Passaggio nascosto — il muro appare intatto |
| **Scale** (stairs) | Simbolo scale | Cambio di livello |

### Distinzione varco vs porta
- **Varco**: due aree comunicano liberamente — il muro si interrompe e basta
- **Porta**: c'è un elemento fisico (porta, cancello, saracinesca) che separa le aree — graficamente una linea trasversale nel passaggio
- Un corridoio (tunnel) è sempre un varco: le sue estremità interrompono i muri delle aree collegate
- Un arco (arch) è un varco decorato — nessuna separazione funzionale

### Unità di misura
- 1 quadretto = 5 feet = 1,5 metri (standard D&D 5e)
- Nel JSON v2: coordinate in quadretti (campo `unit: "sq"`)
- Nella documentazione avventure: formato triplo `Xm / Xft / Xqd`

## Struttura JSON proposta

```json
{
  "meta": {
    "name": "Fogne di Oakshore",
    "style": "sewer",
    "grid": 5,
    "unit": "ft"
  },
  "areas": [
    {
      "id": "ingresso",
      "shape": "rect",
      "x": 0, "y": 0, "w": 10, "h": 30,
      "label": "Galleria d'ingresso",
      "style": "brick",
      "tags": ["tunnel"]
    },
    {
      "id": "cisterna",
      "shape": "circle",
      "cx": 50, "cy": 80, "r": 20,
      "label": "Tana di Korex",
      "style": "stone",
      "tags": ["room", "boss"]
    },
    {
      "id": "sala_taverna",
      "shape": "poly",
      "points": [[0,0],[40,0],[40,30],[0,30]],
      "label": "Sala principale",
      "style": "wood",
      "tags": ["room", "large"]
    }
  ],
  "connections": [
    {
      "from": "ingresso",
      "to": "bivio",
      "type": "tunnel",
      "width": 10
    },
    {
      "from": "sala_taverna",
      "to": "cucina",
      "type": "door"
    }
  ],
  "objects": [
    {
      "area": "cisterna",
      "type": "pillar",
      "pos": "center"
    },
    {
      "area": "ingresso",
      "type": "trap",
      "pos": [5, 15],
      "hidden": true
    }
  ]
}
```

## Tipi di shape

| shape | parametri | uso |
|-------|-----------|-----|
| `rect` | x, y, w, h | stanze, corridoi dritti |
| `circle` | cx, cy, r | cisterne, torri |
| `poly` | points (lista [x,y]) | forme irregolari, caverne |
| `path` | points + width | corridoi curvi, tunnel |

## Tipi di connection

| type | rendering | uso |
|------|-----------|-----|
| `door` | linea con simbolo porta | porte tra stanze |
| `tunnel` | corridoio con larghezza | tunnel fogne, corridoi |
| `arch` | apertura senza porta | archi, passaggi aperti |
| `secret` | invisibile (vista DM) | passaggi segreti |
| `stairs` | simbolo scale | scale, discese |

## Renderer SVG

Il renderer legge il JSON e produce SVG in stile "penna su carta" (oldschool):
- Aree → poligoni con bordo nero, fill leggero
- Connessioni → linee/rettangoli tra le aree
- Oggetti → icone semplici (cerchio per pilastro, X per trappola, ecc.)
- Griglia opzionale (quadretti 5ft)
- Vista DM (tutto) vs vista player (senza segreti/trappole)

## Cosa riusare dal codice esistente

- `dungeon_svg_core.py` — struttura base del renderer, sistema di griglia, get_passages()
- Stili SVG oldschool — colori, tratteggio muri, font
- Sistema `--view dm|players` — già implementato
- Sistema enrichment/oggetti — concetto simile al campo `objects`

## Cosa è nuovo

- Parser JSON v2 (diverso dal formato BSP attuale)
- Renderer forme libere (cerchi, poligoni, path — non solo rettangoli)
- Connessioni come oggetti di primo livello (non derivate dalla griglia)

---

## Sorgenti dalla pipeline v1

Documentazione della pipeline mappe v1 da cui estrarre idee riusabili. Non tutto è applicabile — il v2 è un formato manuale (JSON scritto a mano), non generato proceduralmente.

| Documento | Path | Idee riusabili per v2 |
|-----------|------|----------------------|
| DDL-spec | `tech/rules/DDL-spec.md` | Sistema posizioni (`center`, `against_wall_*`, `corner_*`); gate states (`open`/`closed`/`locked`/`hidden`/`portcullis`/`arch`); merge template+override; seed globale con derivazione per stanza |
| Maps.md | `tech/rules/Maps.md` | Workflow batch con seed; distinzione DM/players; tool manuali come riferimento visivo (DungeonScrawl) |
| MapsPipelineDocs | `tech/rules/MapsPipelineDocs.md` | Architettura base+enrichment separati con merge al volo nel renderer; plugin per gate e oggetti con interfaccia `render(obj,tpl,ox,oy,ow,oh,tile,L)`; check sovrapposizione + `allow_overlap`; ordine rendering (normali prima, overlap dopo) |
| PlanMaps | `tech/rules/PlanMaps.md` | Criteri qualità SlyFlourish (non lineare, loop, ingressi multipli, cross-slice, segreti); modello concettuale esterno/muro/vano; pipeline 5 fasi (topologia→tipizzazione→personalizzazione→vista DM/players→rendering); algoritmi alternativi (Random Walk, Voronoi) |
| RTL-spec | `tech/rules/RTL-spec.md` | Sistema slot obbligatorio/opzionale con conteggio min-max e fill; posizioni in ordine di preferenza; vincoli (`no_overlap`, `clearance_porte`); dimensione minima stanza |

### Idee da valutare per il v2

**Già applicabili ora:**
- Gate states nel campo `connections.type` — il v2 ha già `door`/`tunnel`/`arch`/`secret`, aggiungere `state` (open/closed/locked) come in DDL
- Vista DM/players — `--view dm|players` nel renderer, oggetti con `hidden: true` invisibili in vista players
- Seed per riproducibilità hatching — già implementato nel renderer v2

**Da valutare per fasi successive:**
- Enrichment separato — nel v2 gli oggetti sono inline nel JSON; valutare se separare in un file enrichment per mappe complesse
- Sistema posizioni semantiche — `pos: "center"` già nel v2, estendere con `against_wall_north`, `corner_se` ecc.
- Plugin oggetti — quando il numero di tipi oggetto cresce, passare da rendering inline a plugin come in v1
- Template stanze — applicare un archetipo (taverna, cappella) che popola automaticamente gli oggetti
- Criteri qualità SlyFlourish — utili come checklist per validare mappe scritte a mano (non lineare? loop? segreti?)

---

## Fasi

```
Fase 1 — Formato JSON v2
  Definire lo schema completo
  Scrivere a mano i JSON per i due casi test (fogna + taverna)

Fase 2 — Renderer SVG
  Nuovo script: json2-to-svg.py
  Renderizza aree, connessioni, griglia
  Stile oldschool (penna su carta)

Fase 3 — Test e iterazione
  Generare le mappe per FuoriDaHellfire e LAnelloDelConte
  Iterare su formato e renderer

Fase 4 — Linguaggio naturale → JSON (futuro)
  L'AI legge la descrizione dell'avventura e genera il JSON v2
  Questo è il punto 7 della todo list generale
```

---

## TODO — Renderer

### Connessioni
- [ ] **Spline per corridoi curvi** — shape `path` con punti di controllo, renderer usa curve di Bézier (SVG `<path d="M... C...">`) invece di segmenti dritti. Utile per tunnel naturali, fogne con curve, caverne
- [ ] **Larghezza varco < parete** — il corridoio non deve occupare tutta la facciata della stanza; il varco è più stretto della parete da cui parte (a meno di giustificazione narrativa)
- [ ] **Gate states** — aggiungere campo `state` (open/closed/locked) alle connessioni di tipo `door`, come in DDL v1

### Tassellature per tipo di superficie
La tassellatura (pattern di riempimento intorno alle aree) deve comunicare il tipo di materiale. Ogni stile ha un pattern diverso:

| Superficie | Pattern | Descrizione |
|------------|---------|-------------|
| **Terra/roccia** | Parquet irregolare (attuale) | Linee incrociate a ±45° con jitter — indica terreno solido scavato |
| **Muro costruito** | Mattoni | Rettangoli sfalsati orizzontali — indica muratura |
| **Vuoto/esterno** | Nessuno | Colore di background (bianco) — indica che non c'è nulla |
| **Acqua** | Onde | Linee ondulate orizzontali — canali, pozze |
| **Legno** | Venature | Linee parallele con curve — pavimento taverna |

- [ ] Implementare pattern `brick` (mattoni) per stile `sewer`/`dungeon`
- [ ] Implementare pattern `water` (onde) per canali nelle fogne
- [ ] Implementare pattern `wood` (venature) per taverne/edifici
- [ ] Il campo `style` nell'area JSON seleziona il pattern della tassellatura circostante
- [ ] Il vuoto (celle non coperte da nessuna area e fuori dal raggio di tassellatura) resta bianco — nessun pattern

### Qualità visiva
- [ ] Seed per riproducibilità — già implementato, mantenere
- [ ] SVG → PNG export per Roll20
- [ ] Dimensione quadretto configurabile (attuale: SQ=30px)
