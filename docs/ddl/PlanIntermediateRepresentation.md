# Plan — Intermediate Representation

> Idea approvata. Questo documento raccoglie le decisioni architetturali, le ipotesi di lavoro e le posizioni non convincenti.
> Aggiornato: 2026-04-15 (sessione 7 — osservazioni da test S1, idee generazione descrizioni)

---

## Concetto

Introdurre un livello intermedio tra linguaggio naturale e JSON per la creazione di dungeon.

```
linguaggio naturale
        ↓  (Skill Kiro)
file .ddl  ←── sorgente mantenibile, leggibile da non programmatori
        ↓  (parser Python deterministico o con seed)
dungeon_enrichment.json
        ↓  (renderer esistente)
SVG / PNG
```

---

## Linguaggi

| Nome | Sigla | File | Scope | Stato |
|------|-------|------|-------|-------|
| DungeonDressLang | DDL | `.ddl` | Enrichment (oggetti, gate) su dungeon già generato | In sviluppo |
| RoomTemplateLang | RTL | `.rtl` | Definizione template stanze riutilizzabili | In sviluppo |
| DungeonMakeLang | DML | `.dml` | Topologia dungeon (stanze, connessioni, forma) | Idea futura |

---

## Analisi critica delle posizioni (sessione 2026-04-13)

### Posizioni CONVINCENTI

**1. Non-determinismo necessario**
Il valore di DDL sta nell'astrazione dalle coordinate. Comandi come `riempi di letti` o
`stanza S1 camera da letto` non possono avere un risultato precalcolato: dipendono dalla
geometria della stanza nel `dungeon_base.json`. Il parser deve calcolare quante istanze
entrano e dove metterle. Questo è non-deterministico per costruzione.

**2. DDL con posizioni assolute = JSON mascherato**
Una sintassi tipo `letto in stanza 1 in posizione 2,2 verso sud` non offre alcuna
astrazione rispetto al JSON. L'unico caso in cui le coordinate assolute hanno senso è come
output intermedio del parser, non come input utente.
Il confine utile è: l'utente scrive posizioni *semantiche* (`al centro`, `contro il muro nord`),
il parser calcola le coordinate pixel.

**3. I template procedurali sono il nucleo del valore**
Una `camera da letto` ha letto, comodino, armadio — l'utente non dovrebbe specificarlo.
I template in `tech/templates/rooms/` (attualmente vuoti, gap D4 in PlanMaps.md) sono
la feature principale. Il DDL senza template è solo sintassi alternativa per il JSON di enrichment.

---

### Posizioni NON CONVINCENTI

**"Hash per compressione potente delle mappe"**
Il framing è sbagliato per due motivi:

1. *Il DDL + seed è già la forma compressa.* Il JSON di enrichment è la forma espansa.
   Non esiste una "compressione aggiuntiva" tramite hash — il meccanismo hash/seed
   serve per la riproducibilità, non per ridurre ulteriormente la dimensione.

2. *"Compressione potente" suggerisce che senza hash il DDL non sia già compresso.*
   Un file `.ddl` di 20 righe che descrive 3 stanze è già enormemente più piccolo
   del JSON corrispondente. L'hash serve solo per riottenere le stesse scelte
   non-deterministiche in una sessione successiva — utilità reale ma diversa da compressione.

**Riformulazione corretta:** il DDL + seed è la rappresentazione minimale di un dungeon
arricchito; il JSON è la rappresentazione espansa. Il seed garantisce la riproducibilità
delle scelte non-deterministiche.

---

## Architettura DDL — tre livelli di astrazione

Il DDL supporta tre modalità di specifica per gli oggetti, in ordine decrescente di astrazione:

| Livello | Esempio | Determinismo | Note |
|---------|---------|-------------|------|
| **A — Template procedurale** | `stanza S1 camera da letto` | Non-det (richiede seed) | Applica template completo da `tech/templates/rooms/` |
| **B — Posizione semantica** | `letto contro il muro sud` | Deterministico | Parser calcola coordinate da geometria stanza |
| **C — Coordinate assolute** | `letto in posizione 2,2` | Deterministico | Fuori scope DDL — usare JSON direttamente |

**Solo livelli A e B sono in scope DDL.**

---

## Semantica di merge (Livello A + B)

Quando si specifica sia un tipo stanza (livello A) che oggetti espliciti (livello B),
la regola è:

> Il tipo stanza definisce il **template base**. Gli oggetti espliciti **sostituiscono**
> le istanze dello stesso tipo nel template; oggetti di tipo non presente nel template
> vengono **aggiunti**.

Esempio:
```ddl
stanza S1 camera da letto:
    letto a nord con lenzuola a pois   ← sovrascrive il letto del template
    forziere nell'angolo sud-est       ← aggiunto (non nel template base)
```

Questo è **ipotesi di lavoro** — da validare quando i template rooms saranno definiti.

---

## Semantica "riempi" (ipotesi di lavoro)

```ddl
stanza S3 camerata:
    riempi di letti a castello
```

Comportamento:
1. Il parser legge le dimensioni di S3 dal `dungeon_base.json`
2. Calcola quanti letti a castello (1×2) entrano con spaziatura minima
3. Li distribuisce lungo i muri (orientamento automatico)
4. Se la stanza è troppo piccola per almeno un oggetto: warning nel log, nessun oggetto inserito
5. Richiede seed per riproducibilità dell'ordine di distribuzione

Tipi compatibili con `riempi`: oggetti con dimensione fissa (letto, forziere, colonna).
Non compatibili: oggetti non ripetibili per tipo stanza (altare, fontana).

**Stato: ipotesi di lavoro** — da specificare formalmente in DDL-spec.md v0.2.

---

## Seed per non-determinismo

Il seed del DDL è **separato** dal seed del generatore dungeon.
Proposta: il file `.ddl` può dichiararlo in testa:

```ddl
# seed: 7391
dungeon "Cripta di Malachar":
    ...
```

Se assente, il parser genera un seed casuale e lo stampa nel log (così è riottenibile).

**Stato: ipotesi di lavoro.**

---

## RTL — RoomTemplateLang

### Grammatica core

Il linguaggio core RTL è in **inglese**. I file `.rtl` scritti nel core sono direttamente parsabili da `rtl-to-json.py`. Tipi oggetto e posizioni sono stringhe libere (nessun vocabolario fisso nel parser).

```
template "nome":
    min_size: WxH

    <type> [required | optional] N to M fill: <placements>
    <type> [required | optional] N per <type>: <placements>

    constraints: <list>
    todo: <list>
```

Esempio — bedroom:
```
template "bedroom":
    min_size: 3x3

    bed required 1 to 2 fill: against_wall
    chest optional 1 per bed: corner, against_wall

    constraints: no_overlap
    todo: door_clearance
```

Regole:
- Parole chiave: `template`, `min`, `required`, `optional`, `fill`, `per`, `constraints`, `todo`
- Nomi composti: underscore accettati (`large_table`, `against_wall_north`, `corner_ne`)
- Il `:` finale del header è obbligatorio
- Il `:` prima della lista posizioni è obbligatorio

### Preprocessore (futuro)

Il preprocessore traduce varianti naturali → core RTL. È un layer separato, non parte del parser core.

```
Italiano/naturale                           →  Core RTL
─────────────────────────────────────────────────────
"Un letto è obbligatorio, da 1 a 2 riempi" →  "bed required 1 to 2 fill"
"Il forziere è opzionale, 1 per letto"     →  "chest optional 1 per bed"
"contro il muro"                            →  "against_wall"
"contro il muro nord"                       →  "against_wall_north"
"angolo"                                    →  "corner"
"vincoli"                                   →  "constraints"
"clearance_porte"                           →  "door_clearance"
```

### Decisioni RTL

| # | Decisione |
|---|-----------|
| R1 | Keywords in inglese — il core RTL è lingua-agnostico rispetto al contenuto |
| R2 | Tipi oggetto e posizioni sono stringhe libere; validazione in `template-apply.py` |
| R3 | Il parser RTL è un compilatore di struttura pura, ignaro del dominio |
| R4 | `bedroom.rtl` è un metafile di grammatica (documentazione), non parsato direttamente |
| R5 | Notazione metafile: `(a)` = filler opzionale, `[a, b]` = sinonimi stesso significato, `[a \| b]` = alternative significato diverso |
| R6 | Il preprocessore è il punto unico di traduzione da linguaggio naturale/italiano al core |

### Todo RTL

| # | Feature | Priorità |
|---|---------|----------|
| F1 | Riscrivere `rtl-to-json.py` per grammatica core inglese (stringhe libere, no dizionari) | ✅ fatto |
| F2 | Aggiornare `bedroom.rtl` con grammatica inglese pulita (rimuovere filler italiano) | ✅ fatto |
| F3 | **Preprocessore filler**: traduce italiano/naturale → core RTL | futura |
| F4 | Validazione tipi oggetto contro `tech/templates/objects/*.json` in `rtl-to-json.py` | futura |
| F5 | Fix pluralizzazione `slot_id()`: `stained_glass` → `stained_glasss` (doppia s) — serve un dizionario irregolari o regola euristica | bassa |

---

---

## Limiti attuali del motore di placement

Emersi durante la definizione del template `chapel`. Questi limiti non sono bug — il motore fa quello che è specificato — ma rappresentano semantiche che il linguaggio RTL vuole esprimere e che il motore non sa ancora eseguire.

### L1 — Nessuna awareness delle porte

**Problema:** L'altare va contro il muro senza porte, ma il motore non conosce la posizione delle porte (porte = connessioni in `dungeon_base.json`).

**Effetto attuale:** L'altare finisce contro un muro qualsiasi, potenzialmente bloccando o affiancando una porta.

**Cosa serve:** Il motore deve leggere le connessioni della stanza dal `dungeon_base.json`, calcolare quale lato del muro è occupato da una porta, ed escluderlo (o penalizzarlo) durante il placement.

**Todo RTL:** `altar_prefers_wall_without_door`

**Impatto:** Alto — cambia la struttura di `template-apply.py` (serve accesso alle porte della stanza) e la semantica delle placement preference (aggiungere `against_wall_no_door`).

---

### L2 — Nessun placement relativo tra oggetti

**Problema:** I candelabri vanno *ai lati* dell'altare, ma il motore non conosce la posizione di un oggetto già piazzato per calcolare dove mettere il successivo.

**Effetto attuale:** I candelabri finiscono agli angoli della stanza (prima preference disponibile), non accanto all'altare.

**Cosa serve:** Una nuova famiglia di placement preference: `adjacent_to <slot_id>` (o varianti come `left_of`, `right_of`). Il motore dovrebbe calcolare le celle adiacenti all'oggetto di riferimento e tentare il placement lì.

**Todo RTL:** `candelabra_adjacent_to_altar`

**Impatto:** Alto — richiede un cambio architetturale al motore: `try_place` deve poter ricevere una lista di oggetti già piazzati come riferimento posizionale, non solo come lista di ostacoli.

---

### L3 — Nessuna condizione basata sull'ambiente (finestre, tipo muro)

**Problema:** La vetrata è opzionale *solo se c'è una finestra* sulla parete dell'altare. Il motore non ha accesso a questo tipo di dato (finestre non sono nel `dungeon_base.json`).

**Effetto attuale:** La vetrata viene piazzata come qualsiasi oggetto opzionale — non esiste un meccanismo di "piazza solo se condizione ambientale vera". Confermato empiricamente in S1: la vetrata è finita sul muro est che ha una porta verso S5, dove non può fisicamente esserci una finestra.

**Cosa serve:** Condizioni di placement dipendenti da feature dell'ambiente (finestre, tipo di muro, adiacenza con esterno). Richiede che tali feature siano codificate nel `dungeon_base.json` o in un layer separato.

**Todo RTL:** `stained_glass_requires_window`

**Impatto:** Molto alto — richiede estensione del formato dungeon_base e un sistema di condizioni nel motore. Fuori scope per ora.

---

### Priorità di risoluzione dei limiti

| # | Limite | Impatto semantico | Complessità implementativa | Priorità |
|---|--------|-------------------|---------------------------|----------|
| L1 | Muro senza porte | Alto — altera la leggibilità della stanza | Media — leggere porte da JSON, filtrare muri | Alta |
| L2 | Placement relativo | Alto — candelabri/comodini/oggetti satellite | Alta — refactor architetturale `try_place` | Media |
| L3 | Condizioni ambientali | Medio — solo oggetti opzionali condizionali | Molto alta — richiede nuovo layer dati | Bassa |

---

## Decisioni prese

### Sessione 2026-04-13 — bedroom + RTL design

| # | Decisione |
|---|-----------|
| D1 | Template = definizione generale + riempimento con constraint, senza sottocategorie per ora |
| D2 | Constraint generali: no overlap tra oggetti |
| D3 | Constraint specifici bedroom: max 2 letti, 1 forziere per letto effettivamente piazzato |
| D4 | Letti: contro un muro (l'ordine dei muri è randomizzato dal seed) |
| D5 | Forzieri: in un angolo o contro un muro |
| D6 | Degradazione: se oggetto required non entra → warning nel log + proposta modifica minima (non auto-applicata) |
| D7 | Clearance davanti alle porte: rimandato, aggiunto a todo |
| D8 | Proof of concept: `tech/templates/rooms/bedroom.json` — primo template definito |

### Sessione 2026-04-13 — chapel + analisi limiti

| # | Decisione |
|---|-----------|
| D9 | Secondo template `chapel.json` definito — oggetti: altare, candelabra (2 per altare), vetrata (opzionale) |
| D10 | Nuovi oggetti aggiunti: `candelabra.json` (1×1), `stained_glass.json` (2×1) |
| D11 | I tre limiti del motore (L1 muro-senza-porte, L2 placement-relativo, L3 condizioni-ambiente) sono classificati e documentati esplicitamente come architettura futura — non workaround |
| D12 | La vetrata rimane nel template come oggetto opzionale senza condizione finestra: approssimazione accettabile finché L3 non è implementato |
| D13 | `stained_glass_requires_window` non va in `constraints` (vincoli già implementati) ma in `todo_constraints` — distinzione semantica preservata nel JSON |

### Sessione 2026-04-15 — osservazioni da test S1

| # | Decisione |
|---|-----------|
| D21 | **Bug `next_to` non è "ai lati"**: `next_to altar` piazza in qualsiasi cella adiacente, non specificamente a sinistra e destra lungo il lato lungo. I candelabri devono stare ai lati dell'altare rispetto al suo asse lungo. Serve una nuova preference: `left_of <type>` / `right_of <type>` o `beside <type>` che consideri l'orientamento dell'oggetto di riferimento. |
| D22 | **Idea — generatore descrizioni testuali**: uno script `enrichment-to-description.py` che legge `dungeon_enrichment.json` e produce testo in linguaggio naturale per ogni stanza. Input: tipo stanza + lista oggetti effettivi + porte. Output: paragrafo narrativo. Prerequisito utile: vocabolario per-oggetto (frasi descrittive in `objects/*.json`). |
| D23 | **Idea — descrizione da oggetti reali, non da tipo stanza**: la descrizione generata deve riferirsi agli oggetti *effettivamente piazzati* (altare, 2 candelabri, vetrata), non al nome tecnico della stanza ("chapel"). Il tipo stanza è un tag per il motore, non per il giocatore. |

### Sessione 2026-04-14 — bug fix placement, near_wall/next_to, struttura build

| # | Decisione |
|---|-----------|
| D14 | `directional_axis: "parallel"` aggiunto a `altar.json` e `bookshelf.json` — il lato lungo corre parallelo al muro invece di perpendicolare |
| D15 | `near_wall of <dir>`: distanza 1–2 dal muro, scelta casuale con fallback sull'altra; `against_wall` = `near_wall` distanza 0 — entrambi usano `_place_near_wall()` come core |
| D16 | `next_to <type>`: placement adiacente a oggetti già piazzati dello stesso tipo — genera tutte le celle adiacenti, shuffled, e prova in ordine |
| D17 | Sintassi senza parentesi: `near_wall of north` (non `near_wall(north)`) — il risultato finale deve sembrare linguaggio naturale |
| D18 | Sorgenti RTL e JSON oggetti in `tech/templates/` (committati); JSON compilati da RTL in `tech/build/rooms/` (gitignored via `.gitignore`) |
| D19 | Il titolo del dungeon scritto nel DDL (`dungeon "Nome":`) fluisce in `enrichment["title"]` e da lì nell'SVG — il dungeon_base.json non è più la fonte del titolo |
| D20 | `coin_pile_oldschool.py` creato: plugin obbligatorio per rendere visibili gli oggetti nell'SVG — senza plugin il renderer piazza l'oggetto ma non lo disegna |

---

## Domande aperte (da risolvere prima di implementare)

| # | Domanda | Impatto |
|---|---------|---------|
| Q1 | Merge A+B: sostituzione o aggiunta? (vedi sopra — ipotesi attuale: sostituzione per stesso tipo) | Semantica parser |
| Q2 | `riempi` con stanza troppo piccola: warning-e-continua o errore-e-stop? | UX |
| Q3 | Template rooms JSON: includono coordinate o solo lista oggetti con posizione semantica? | Formato file |
| Q4 | Se nessun tipo stanza è dichiarato e ci sono solo oggetti espliciti, il seed serve? | Implementazione |
| Q5 | `di solito` come keyword esplicita vs come comportamento implicito del tipo (template = default) | Sintassi |

---

## Template stanze — stato

I sorgenti RTL sono in `tech/templates/rooms/*.rtl` (committati).
I JSON compilati sono in `tech/build/rooms/*.json` (gitignored — rigenerare con `rtl-to-json.py`).

| Template | Oggetti definiti | Stato |
|----------|-----------------|-------|
| `bedroom` | letto (fill against_wall), forziere (next_to bed) | ✅ fatto |
| `chapel` | altare (near_wall\|center), candelabra (2 per altare), vetrata (opzionale) | ✅ fatto |
| `dragon_treasury` | coin_pile (4×4) al centro | ✅ fatto |
| `demonic_shrine` | pentacolo (calpestabile), altare (sovrapposto, overlap), tuniche/maschere | ✅ fatto |

**Oggetti disponibili** in `tech/templates/objects/`: altar, bed, bookshelf, candelabra, chest, coin_pile, column, demonic_pentacle, fountain, large_fountain, large_table, mask, robe, stained_glass, table.

### Note su `dragon_treasury`

Una sola pila di monete 4×4 al centro. Il drago è un personaggio, non un oggetto di arredamento — sarà gestito da un altro layer del progetto. Il campo `todo: dragon_on_top` nel `.rtl` segnala questa dipendenza futura.

Dimensione minima 6×6 per garantire che la pila (4×4) abbia almeno 1 quadretto di margine su ogni lato.

### Note su `demonic_shrine`

- 1 pentacolo demoniaco al centro (5×5, calpestabile, obbligatorio)
- 1 altare al centro sovrapposto al pentacolo (slot con `allow_overlap: true`, opzionale)
- 2–4 tuniche nere alle pareti (fill, opzionale) — sostituibili con maschere via override DDL (`has mask at against_wall`)
- Il demone/cultista è un personaggio, non un oggetto arredamento — `todo: demon_on_altar`
- Dimensione minima 7×7 per garantire margine attorno al pentacolo 5×5

---

## Sequenza di implementazione

```
1. Template rooms — stati
   → bedroom          ✅ (letto fill against_wall, forziere next_to bed)
   → chapel           ✅ (altare near_wall|center, candelabra, vetrata opzionale)
   → dragon_treasury  ✅ (coin_pile 4×4 al centro)
   → demonic_shrine   ✅ (pentacolo + altare sovrapposto + tuniche)

2. Motore placement — stati
   → allow_overlap (keyword RTL `overlap`)              ✅ fatto
   → near_wall of <dir> (distanza 1–2, fallback)        ✅ fatto
   → next_to <type> (adiacente a oggetti piazzati)      ✅ fatto
   → directional_axis parallel (lato lungo sul muro)    ✅ fatto
   → against_wall_no_door / near_wall_no_door (L1)      ✅ fatto
   → beside <type> (ai lati lungo l'asse lungo) (D21)   [ ] media priorità
   → Risoluzione limiti L2 completa (adjacent_to)       [ ] media priorità

3. Struttura file — stati
   → RTL in tech/templates/rooms/ (committati)          ✅ fatto
   → JSON compilati in tech/build/rooms/ (gitignored)   ✅ fatto
   → .gitignore con tech/build/                         ✅ fatto

4. Pipeline SVG — stati
   → Titolo SVG dal DDL (via enrichment["title"])       ✅ fatto
   → Plugin coin_pile_oldschool.py                      ✅ fatto
   → Plugin mancanti per altri oggetti                  [ ] da verificare

5. DDL — stati
   → Spec v0.3 (struttura a blocchi, English keywords)  ✅ fatto
   → Parser ddl-to-enrichment.py v0.2                   ✅ fatto
   → Direttive: is a, has, door to                      ✅ fatto
   → Risoluzione gate room_id → passage coordinates     ✅ fatto
   → Semantica "riempi" (fill verb in DDL)              [ ] da specificare in DDL-spec v0.4
   → Semantica merge A+B con sostituzione               [ ] Q1 aperta

6. Generazione descrizioni testuali (D22, D23)
   → enrichment-to-description.py                       [ ] idea approvata, da progettare
   → Vocabolario descrittivo per-oggetto (objects/*.json) [ ] aggiungere campo "description_in_room"
   → Output: paragrafo per stanza da oggetti reali       [ ] non dal tipo-stanza

6. Skill Kiro → produce .ddl da linguaggio naturale
   → Prerequisito: DDL stabile e documentato

7. [Bassa priorità] Risolvere limite L3 (condizioni ambientali)
   → Richiede feature muri nel dungeon_base.json
```

---

## Riferimenti

- `tech/rules/DDL-spec.md` — specifica sintattica DungeonDressLang
- `tech/rules/PlanMaps.md` — pipeline mappe
- `tech/rules/MapsPipelineDocs.md` — documentazione tecnica script e formato JSON
- `tech/templates/rooms/` — sorgenti RTL template stanze
- `tech/templates/objects/` — JSON definizioni oggetti + plugin renderer `*_oldschool.py`
- `tech/build/rooms/` — JSON compilati (gitignored, rigenerare con `rtl-to-json.py`)
- `tech/reports/example_crypt.ddl` — DDL di riferimento per test e debug pipeline
