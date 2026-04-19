# Plan Mappe — Generatore Dungeon Custom

Piano di sviluppo per `tech/scripts/generate-dungeon.py`.
Versione BSP archiviata in `tech/scripts/generate-dungeon-bsp-0.1.py`.

---

## Modello concettuale del dungeon

Un dungeon è composto da tre elementi strutturali:

| elemento | descrizione | colore debug |
|----------|-------------|--------------|
| **Esterno** | Spazio fuori dal dungeon | bianco |
| **Muro** | Separa vani tra loro (interno) o vani dall'esterno (esterno) | nero/grigio |
| **Vano** | Spazio interno percorribile (stanza o corridoio) | giallo/arancione |

**La compattezza si applica ai vani in generale** — tutti i vani (stanze e corridoi) devono essere adiacenti tra loro, separati da muri di 1 quadretto.

### Tipi di spazio interno

**Stanza** — spazio percorribile destinato ad essere abitato/arredato. Dimensione tipica: 4x4 quadretti o più. Ha almeno una porta.

**Corridoio** (anche: atrio, andito, anticamera) — vano chiuso con queste caratteristiche:
- La dimensione minore (larghezza) è 1-3 quadretti, indipendentemente dall'orientamento (orizzontale o verticale)
- Rapporto larghezza:lunghezza ≤ 1:3 circa (la dimensione minore è molto più piccola di quella maggiore)
- Serve esclusivamente come passaggio — non ha funzione propria, non è arredato
- Ha almeno due aperture (porte) alle estremità
- Lo spazio totale occupato da corridoi è piccolo rispetto al dungeon: indicativamente < 1/5 della superficie totale percorribile

**Nota:** un'apertura diretta nel muro condiviso tra due stanze adiacenti è una **porta**, non un corridoio. Un corridoio è un vano separato con proprie pareti.

**Porta** — apertura in un muro (interno o esterno) che collega due spazi adiacenti. Non è uno spazio, è un elemento del muro. Larghezza tipica: 1-2 quadretti.

### Distinzione porta vs corridoio
- **Porta**: due stanze condividono un muro → apertura diretta nel muro condiviso
- **Corridoio**: due stanze non sono adiacenti → spazio stretto che le collega, con porte alle estremità

### Tipi di muro
- **Muro interno**: separa due stanze o una stanza da un corridoio. Spessore tipico: 1 quadretto.
- **Muro esterno**: separa una stanza dall'esterno. Spessore tipico: 1-2 quadretti.

### Perimetro
Il dungeon ha un perimetro definito (attualmente: rettangolare).
Evoluzione futura: perimetro irregolare, dungeon divisi in blocchi collegati da corridoi esterni.

---

## Approccio attuale: cell-grid

La mappa è divisa in una griglia di celle-vano di dimensione variabile.
Ogni cella è separata dalle adiacenti da 1 quadretto di muro.
Un sottoinsieme di celle viene attivato (vani) e connesso tramite **BFS dal centro**.
Le celle non attivate rimangono muro.
Le connessioni tra vani sono basate su **adiacenza fisica** (overlap reale tra celle).

**Limite attuale:** le celle della griglia sono tutte di tipo "stanza". I corridoi vengono aggiunti come strisce CORR dopo la generazione, non come celle della griglia — quindi non sono vani veri (gap #8).

**Unità di misura:** 1 quadretto = 5 feet = 1,5 metri (standard D&D 5e).

---

## Riferimento di qualità

- `goodExamples/maps/dungeon_automatico.png` — stile old-school (Watabou/donjon), target strutturale
- `goodExamples/maps/dungeon_grafica_plus.png` — target grafico finale (workflow Gemini, non replicabile nello script)

Caratteristiche del riferimento da replicare:
- Muri con texture hatching, distinti dall'esterno
- Layout compatto, stanze adiacenti con 1 muro tra loro
- Corridoi larghi 1-2 quadretti con griglia visibile
- Porte marcate sui muri
- Griglia sul pavimento
- Forme stanze variabili
- Perimetro esterno riconoscibile

---

## Criteri di qualità (fonte: SlyFlourish + Jaquaying the Dungeon)

| criterio | descrizione | stato attuale |
|----------|-------------|---------------|
| Non lineare | I PG vedono la stanza finale senza poterci arrivare direttamente | ❌ |
| Loop | Percorsi circolari (A→B→C→A) | ❌ |
| Ingressi multipli | Almeno 2 entrate/uscite verso l'esterno | ❌ (1 implementato) |
| Cross-slice | Elemento divisore (fiume, burrone) | ❌ |
| Segreti | Passaggi nascosti | ❌ |
| Dimensione giusta | 12-30 stanze | ✅ configurabile |
| Stanze uniche | Forme e contenuti distintivi | ⚠️ solo colore speciale |
| Mix pietra + naturale | Varietà morfologica | ❌ solo rettangoli |
| Perimetro definito | Confine esterno riconoscibile | ✅ |

---

## Gap da colmare (priorità)

| # | problema | soluzione | stato |
|---|----------|-----------|-------|
| 1 | Nessun perimetro esterno | bordo rettangolare; esterno = bianco, muro esterno = nero | ✅ |
| 2 | Stanze isolate | BFS dal centro garantisce cluster connesso | ✅ |
| 3 | Stanze troppo regolari | range room_min/room_max diretto | ✅ |
| 4 | Nessun corridoio come vano | corridoi aggiunti come strisce CORR (soluzione parziale, non vani veri della griglia) | ⚠️ parziale → vedi gap #8 |
| 5 | Nessun ingresso verso esterno | porta sul muro esterno della stanza entrance | ✅ |
| 6 | Angoli corridoio non chiusi | muri laterali non si raccordano agli angoli | ⚠️ non grave |
| 7 | Nessun loop | connessioni extra tra stanze adiacenti non già connesse | ⚠️ minore |
| 8 | Corridoi non sono vani della griglia | celle-corridoio nella griglia + flood-fill per unire celle contigue | ✅ |
| 9 | Edge BFS basati su matrice, non su adiacenza fisica | spanning tree basato su overlap fisico tra stanze | ✅ |
| 10 | Stanze solo rettangolari | forme L/T o stanze con rientranze | [ ] |
| 11 | Nessun cross-slice | elemento divisore opzionale | [ ] |

---

## Feature già implementate (cell-grid-0.3)

- [x] Griglia di celle con dimensioni variabili (room_min/room_max diretti)
- [x] Celle-corridoio nella griglia (`--corridor-rows N`)
- [x] Unificazione celle-corridoio contigue in un unico vano (flood-fill)
- [x] BFS dal centro per selezione vani connessi e compatti
- [x] Spanning tree basato su adiacenza fisica (overlap reale tra vani)
- [x] Porte tra vani fisicamente adiacenti (apertura nel muro condiviso)
- [x] Corridoi tra vani non adiacenti (strisce CORR con muri laterali)
- [x] Hatching sui muri
- [x] Griglia sul pavimento
- [x] Porte visibili sulle aperture
- [x] Distinzione muro esterno (nero) / muro interno (grigio)
- [x] Corridoi arancioni distinti dalle stanze gialle
- [x] Esterno bianco per costruzione (griglia inizializzata EXTERIOR)
- [x] Porta verso esterno automatica (vano con max esposizione)
- [x] Rilevamento automatico porte esterne su tutti i vani
- [x] Centramento mappa nel canvas
- [x] Titolo parametrico (`--title`) con copyright e data
- [x] Etichette S1/S2... per stanze, C1/C2... per corridoi
- [x] Export JSON strutturato (vani, corridoi, connessioni)
- [x] Export MD con descrizione placeholder per ogni vano
- [x] Versione archiviata: `generate-dungeon-cell-grid-0.3.py`

---

## Todo futuri

### A) Topologia — complessità strutturale
- [ ] Loop (percorsi circolari A→B→C→A) — minore
- [ ] Ingressi multipli verso l'esterno
- [ ] Stanze con forme non rettangolari (L, T, poligonali)
- [ ] Corridoi verticali (attualmente solo orizzontali)
- [ ] Stanze dentro stanze (non ricorsive, con porta interna)
- [ ] Dimensione minima stanza: 2 quadretti (2x1 o 2x2)
- [ ] Cross-slice (elemento divisore: fiume, burrone, crollo)

### B) Varianti topologiche non architetturali
- [ ] Caverna: celle con forma irregolare (Cellular Automata o Random Walk)
- [ ] Chiesa/tempio: layout assiale con navata centrale e cappelle laterali
- [ ] Torre: layout verticale multi-piano (scale tra piani)
- [ ] Dungeon divisi in blocchi collegati da corridoi esterni
- [ ] Perimetro irregolare (dopo stabilizzazione rettangolare)

### C) Grafica — opzioni senza servizi esterni
- [x] **JSON → SVG tileset** (`json-to-svg.py` v0.1): tileset DCSS integrati, porte dal JSON, header grafico. Archiviato: `json-to-svg-0.1.py`
- [x] **JSON → SVG old-school** (`json-to-svg-oldschool.py` v0.1): hatching random B&W, griglia pavimento, bordi neri. ⚠️ difetti visivi da correggere
- [x] **JSON → Tiled TMX** (`json-to-tmx.py`): implementato, apribile in Tiled Map Editor su Windows

**Refactoring grafica (da fare prima di P2/P3/P4):**
- [x] Estrarre codice comune in `dungeon_svg_core.py` (rebuild_grid, porte, etichette, bounding box)
- [x] `json-to-svg.py` v0.2 e `json-to-svg-oldschool.py` v0.2 usano il core comune
- [ ] Aggiungere `cairosvg` per export SVG → PNG automatico (`--export-png`)

**Fix JSON generatore (generate-dungeon.py):**
- [ ] Rimuovere campo `corridors` (sempre vuoto, i corridoi sono in `rooms`)
- [ ] Aggiungere `cell_size` e `wall_thickness` ai metadati
- [ ] Fix `doors[]`: includere anche aperture dirette tra stanze adiacenti (non solo CORR→FLOOR)
- [ ] Garantire `grid_size` sempre presente (già fatto in 0.3, verificare)

**Prototipi grafici:**
- [x] **OLDSCHOOL** v0.3 — enrichment (forzieri, finestre), porte corrette, snap griglia. Archiviato: `json-to-svg-oldschool-0.3.py`
- [x] **STONE** v0.1 — texture pietra procedurale Pillow, sfondo scuro, porte denti dorati. Archiviato: `json-to-svg-stone-0.1.py`
- [x] **KENNEY** v0.1 — tileset Kenney Scribble, porte corrette. Archiviato: `json-to-svg-kenney-0.1.py` ⚠️ angoli muri da migliorare (sperimentale)
- [ ] **P3 — Procedurale pietra** (Pillow texture generata, nessun asset esterno)
- [x] **BLUEPRINT** v0.1 — carta millimetrata, hatching blu, linee jitter, font corsivo. Archiviato: `json-to-svg-blueprint-0.1.py`
- [ ] Arredamento (botti, casse, tavoli) — versioni future dopo stabilizzazione stili

**Skill Kiro (dopo stabilizzazione script):**
- [ ] `generate-dungeon` skill: parametri CLI, output JSON/PNG/MD
- [ ] `json-to-svg` skill: stili disponibili, tileset, export PNG
- [ ] Documentazione completa in `tech/how-to/HowToMaps.md`

### D) Arricchimento mappe

---

#### Pipeline di creazione mappa — descrizione concettuale

Questa è la sequenza logica per produrre una mappa giocabile, indipendentemente dagli strumenti usati.

**1. Topologia**
Si decide la struttura del dungeon: quante stanze, come sono collegate, dove si trovano le porte, quale è l'ingresso. Il risultato è uno scheletro geometrico — stanze con dimensioni e connessioni, senza ancora un contenuto.

**2. Tipizzazione**
A ogni stanza si assegna un *tipo* che descrive la sua funzione narrativa: cappella, camera da letto, santuario, stanza dei tesori. Il tipo attiva un *template* che popolerà automaticamente la stanza con gli oggetti appropriati e le loro posizioni di default.

**3. Personalizzazione**
Si aggiungono elementi specifici dell'avventura che vanno oltre il template: una porta segreta che non è nel template, un oggetto narrativamente rilevante, una porta sbarrata tra due stanze precise. Questi si sovrappongono al template senza sostituirlo.

**4. Vista DM vs giocatori**
La stessa mappa esiste in due versioni: quella del master (con segreti, note, passaggi nascosti) e quella dei giocatori (solo ciò che vedono). La distinzione è applicata al volo — non esistono due file separati.

**5. Rendering**
La mappa viene generata nello stile visivo scelto: old-school, blueprint, pietra, isometrico. Lo stile è decorativo — non cambia la struttura logica.

---

**Pipeline tecnica:**
```
generate-dungeon.py (cell-grid)
        ↓
dungeon_base.json + dungeon_base.png (debug)
        ↓
dungeon_enrichment.json  ←  .ddl (DungeonDressLang)  ←  .rtl (template stanze)
        ↓
renderer (OLDSCHOOL | BLUEPRINT | KENNEY | STONE)  +  --view dm|players
        ↓
     SVG → PNG
```

**Architettura JSON:**
- `dungeon_base.json` — struttura griglia pura. Generato da `generate-dungeon.py`.
- `dungeon_enrichment.json` — arredamento, oggetti, gate, note. Indipendente dalla grafica.

**Nota:** il merge avviene al volo nel renderer con `--enrichment` e `--view dm|players`. Non esistono file separati DM/players su disco.

**Decisioni:**
- [x] D1: `dungeon_dm.json` è file separato ✅ — ma merge layer non ancora implementato, vedi sotto
- [x] D2: Posizione oggetti — coordinate in quadretti relativi alla stanza (x, y interi) ✅
- [ ] D3: Skill Kiro modifica `dungeon_enrichment.json`, mostra preview prima di applicare — **marcato ✅ per errore, non implementato**
- [ ] D4: Template stanza — file JSON pluggabili in `tech/templates/rooms/` — **marcato ✅ per errore, cartella vuota**
- [x] D5: Versione giocatori — flag `--view dm|players` al renderer ✅

**Modi di creare dungeon_enrichment.json:**
- [ ] Manuale — documentazione struttura JSON
- [ ] Wizard CLI — script interattivo stanza per stanza
- [ ] Template automatico — tipi stanza predefiniti (biblioteca, camera, prigione...)
- [ ] Skill Kiro — linguaggio naturale: "aggiungi una libreria a S3"

**Renderer arricchito (OLDSCHOOL):**
- [x] Forziere (chest) — 1×1, serratura, jitter
- [x] Colonna (column) — 1×1, cerchio con punto, jitter
- [x] Altare (altar) — 2×1, croce, jitter
- [x] Letto (bed) — 1×2, direzionale, cuscino, sheet_type plain|dots, fill grigio, jitter
- [x] Libreria (bookshelf) — 1×2, direzionale, linee verticali, jitter
- [x] Tavolo (table) — 2×1, gambe tonde, fill grigio, diagonali texture, jitter
- [x] Tavolo grande (large_table) — 2×4, stesso stile di table
- [x] Fontana (fountain) — 2×2, cerchi concentrici, zampillo
- [x] Fontana grande (large_fountain) — 4×4, stesso stile di fountain
- [x] Pentacolo demoniaco (demonic_pentacle) — 5×5
- [x] Finestre — trattino tratteggiato sul muro esterno (no sovrapposizione porte)
- [x] Architettura plugin: `tipo_oldschool.py` per ogni oggetto, motore carica dinamicamente
- [x] Check sovrapposizione oggetti — warning + skip; flag `allow_overlap` per eccezioni
- [x] Ordine rendering: oggetti normali prima, `allow_overlap` sopra
- [x] Refactoring `doors` → `passages` — nomenclatura coerente in tutto il progetto
- [x] `width` nei passages del JSON base (numero di celle consecutive)
- [x] Fix raggruppamento passage (bug orient 'v' — celle consecutive su asse sbagliato)
- [x] Sistema gate — plugin `gate_oldschool.py`, template in `tech/templates/gates/`
  - Tipi: `door` (open/closed/locked), `portcullis` (open/closed), `arch` (open), `secret` (hidden/found)
  - Gate nell'enrichment: `"gates": [{"x":N,"y":N,"type":"door","state":"closed"}]`
  - Passage senza gate in enrichment → default `door closed`
- [x] Vista DM vs players (`--view dm|players`) — secret hidden/found invisibile in players
- [x] Documentazione tecnica — `tech/rules/MapsPipelineDocs.md`
- [ ] *(minor)* Grafica passage/gate da rivedere — qualità attuale mediocre
- [x] Validazione enrichment — check oggetti/stati inesistenti al caricamento ✅
- [ ] Sistema stati oggetti (es. chest: open/closed/locked) — da rimandare
- [ ] *(minor)* SVG → PNG — serve per Roll20; indagare: ottimizzazione per Roll20, possibilità di includere vista DM e players nello stesso file
- [ ] Validazione oggetti/stati inesistenti al caricamento enrichment — da cancellare?
- [ ] Sistema stati per oggetti (es. chest: open/closed/locked) — da cancellare?
- [ ] Estendere enrichment a BLUEPRINT e STONE
- [ ] *(esperimento)* Renderer isometrico `json-to-svg-iso.py` — prototipo funzionante, da sviluppare
- [ ] Wizard CLI per arricchimento interattivo — da rivalutare dopo DDL (potrebbe diventare superfluo)
- **DungeonDressLang (DDL)** — linguaggio semi-naturale per enrichment
  - [x] Spec v0.3 — struttura a blocchi, keywords inglesi (`DDL-spec.md`)
  - [x] Parser `ddl-to-enrichment.py` v0.2 — `is a`, `has`, `door to`, risoluzione gate
  - [x] Template stanze: `bedroom`, `chapel`, `dragon_treasury` — dettaglio in `PlanIntermediateRepresentation.md`
  - [ ] Template stanze: `demonic_shrine` (bloccato su allow_overlap nel motore)
  - [ ] Skill Kiro → DDL (linguaggio naturale → .ddl → JSON)
- [ ] **DungeonMakeLang (DML)** — topologia dungeon in linguaggio semi-naturale, idea futura molto complessa
- [ ] **Clearance davanti alle porte** *(proposta, rimandato)* — constraint: nessun oggetto nella cella/e immediatamente davanti a un passage. Richiede che il placement engine conosca le coordinate dei passage della stanza dal `dungeon_base.json`.

---

## Algoritmi di generazione — analisi e casi d'uso

| algoritmo | descrizione | quando usarlo | rilevanza per noi |
|-----------|-------------|---------------|-------------------|
| **BSP (Binary Space Partitioning)** | Divide ricorsivamente l'area in rettangoli, poi connette con corridoi | Dungeon con stanze ben definite, layout ordinato, struttura ad albero | ⚠️ Usato e archiviato (bsp-0.1). Buono per struttura, ma genera sempre alberi (no loop) e stanze proporzionali alle partizioni |
| **Cell-grid + BFS/MST** | Griglia di celle di dimensione variabile, BFS seleziona un sottoinsieme connesso | Dungeon con stanze di dimensioni variabili, layout compatto, controllo sul numero di stanze | ✅ Approccio attuale. Gap aperto: celle della griglia sono solo stanze, non corridoi (gap #8) |
| **Algoritmo basato su Grafo** | Definisce prima la struttura logica (grafo stanze+connessioni), poi piazza fisicamente le stanze rispettando il grafo | Quando la narrativa determina la struttura (es. "la stanza del boss deve essere raggiungibile solo dopo la stanza chiave") | 🔮 Utile per avventure con struttura narrativa forte. Da valutare per future versioni |
| **Random Walk (Drunkard's Walk)** | Un punto cammina casualmente scavando tunnel | Corridoi organici, dungeon labirintici, caverne con passaggi irregolari | 🔮 Utile per generare corridoi più naturali tra stanze già posizionate (alternativa ai corridoi a L) |
| **Cellular Automata** | Simula crescita/morte di celle in base ai vicini | Caverne naturali, aree aperte irregolari, zone "selvagge" | ❌ Non adatto per dungeon con stanze definite. Utile solo se vogliamo aggiungere zone-caverna |
| **Dice Drop** | Lancia dadi virtuali su una mappa per posizionare stanze | Variabilità organica nella posizione delle stanze, layout non simmetrico | 🔮 Interessante per posizionare stanze in modo meno regolare della griglia. Combinabile con BFS per la connessione |
| **Voronoi / Delaunay** | Divide lo spazio in regioni basate su punti casuali, usa Delaunay per i corridoi | Layout organico con stanze di forma irregolare, corridoi che seguono percorsi naturali | 🔮 Avanzato. Utile se vogliamo stanze non rettangolari e corridoi curvi |

### Raccomandazioni per evoluzioni future

- **Corridoi più naturali**: sostituire i corridoi a L con Random Walk limitato
- **Struttura narrativa**: aggiungere un layer "grafo logico" sopra il cell-grid per vincoli narrativi (es. stanza boss sempre alla fine)
- **Zone caverna**: Cellular Automata per aree specifiche del dungeon (es. una sezione naturale vs una sezione costruita)
- **Layout meno regolare**: Dice Drop per il posizionamento iniziale delle stanze, poi BFS per la connessione

---

## Storico iterazioni (riassunto)

| iter | approccio | seed | stanze | esito principale |
|------|-----------|------|--------|-----------------|
| 1-6 | BSP padding | 42 | 13-30 | progressivi miglioramenti visivi (hatching, griglia, porte, cap stanze) ma layout sempre sparso → cambio approccio |
| 7 | cell-grid v1 | 42 | 12 | stanze sparse, DFS seleziona celle lontane |
| 8 | cell-grid + densità auto | 42 | 12 | layout compatto, manca perimetro esterno |
| 9 | + esterno bianco/muri neri | 42 | 12 | tre elementi distinti visibili, stanze isolate in seed 42 |
| 10 | + muri int/ext distinti | 42 | 12 | muri esterni neri, interni grigi, stanze giallo chiaro |
| 11 | + griglia EXTERIOR per costruzione | 42 | 12 | esterno bianco corretto, layout ottimo seed 123 |
| 12 | + centramento + porta esterno (v1) | 42 | 12 | centramento ok, porta non visibile (entrance non sul bordo) |
| 13 | + BFS dal centro | 42 | 12 | nessuna stanza isolata, porta ancora non visibile |
| 14-16 | fix porta esterno (3 tentativi) | 42 | 12 | porta trovata ma non visibile o entrance non sul bordo |
| 17 | entrance = stanza con max esposizione | 42 | 12 | porta verso esterno visibile ✅ |
| 18 | + titolo parametrico | 42 | 12 | titolo "Test Dungeon" in basso ✅ |
| 19 | + corridoi tra stanze non adiacenti + varietà stanze | 42 | 12 | corridoi visibili ✅, stanze più variabili ✅ |
| 20-23 | fix JSON: connessioni false, porte esterne, edge fisici | 42 | 12 | JSON coerente con PNG ✅ → **versione stabile cell-grid-0.2** |
| 24-29 | corridoi come vani della griglia, unificazione flood-fill, speciali disabilitati | 42 | 9+1C | corridoio C1 unificato ✅, JSON coerente ✅ → **versione stabile cell-grid-0.3** |
