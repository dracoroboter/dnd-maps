# DungeonDressLang (DDL) — Specifica v0.3

> Linguaggio semi-naturale per descrivere l'enrichment di un dungeon già generato.
> File: `.ddl` — prodotto manualmente o dalla Skill Kiro, convertito in `dungeon_enrichment.json`.
> v0.3: struttura a blocchi indentati (coerente con RTL). Keywords in inglese.

---

## Input / Output

```
dungeon_base.json  +  enrichment.ddl
                            ↓
                  ddl-to-enrichment.py
                            ↓
               dungeon_enrichment.json
```

---

## Struttura generale

```ddl
# seed: N

dungeon "title":

    <ID> [is a <template>]:
        has <type> at <position>
        door to <ID> is <state>

    <ID> [is a <template>]
```

Regole strutturali:
- **Indentazione** — definisce la gerarchia (4 spazi o 1 tab; consistente nel file)
- **`:`** — obbligatorio se il blocco ha un corpo; opzionale se la riga è autonoma
- **Commenti** — righe che iniziano con `#`
- **`# seed: N`** — riga speciale: imposta il seed del generatore
- **Case-insensitive**
- Se il seed è assente il parser ne genera uno casuale e lo stampa nel log

---

## Blocco dungeon (header opzionale)

```ddl
dungeon "Crypt of Malachar":
```

La riga `dungeon` è opzionale — serve solo come intestazione leggibile.
Se assente il parser usa il nome del file `.ddl`.

---

## Blocco stanza

```ddl
S1 is a chapel:
    ...

S4 is a bedroom

S2:
    has bed at against_wall_north
```

- `<ID>` deve corrispondere a un ID nel `dungeon_base.json`
- `is a <template>` è opzionale — se presente applica il template procedurale (Livello A)
- Il `:` finale è necessario solo se il blocco ha un corpo indentato
- Una stanza senza template e senza corpo è ignorata (warning nel log)

### Template disponibili (v0.3)

| Keyword DDL | File template |
|-------------|---------------|
| `bedroom` | `bedroom.json` |
| `chapel` | `chapel.json` |
| `dragon_treasury` | `dragon_treasury.json` |
| `demonic_shrine` | *(da creare)* |

---

## Direttive nel corpo stanza

### `has <type> at <position>` — oggetto esplicito (Livello B)

```ddl
has bed at against_wall_north
has chest at corner_se
has demonic_pentacle at center
```

- `<type>` deve corrispondere a un file `tech/templates/objects/<type>.json`
- `<position>` usa le stesse stringhe del placement engine RTL (vedi tabella)
- L'oggetto viene piazzato con overlap check contro gli oggetti già presenti
- Se non c'è spazio: warning nel log, oggetto saltato

#### Posizioni disponibili

| Posizione | Significato |
|-----------|-------------|
| `center` | Centro geometrico |
| `against_wall` | Qualsiasi muro (seed sceglie) |
| `against_wall_north` | Muro nord, centrato |
| `against_wall_south` | Muro sud, centrato |
| `against_wall_east` | Muro est, centrato |
| `against_wall_west` | Muro ovest, centrato |
| `corner_any` | Qualsiasi angolo (seed sceglie) |
| `corner_ne` | Angolo nord-est |
| `corner_nw` | Angolo nord-ovest |
| `corner_se` | Angolo sud-est |
| `corner_sw` | Angolo sud-ovest |

---

### `door to <ID> is <state>` — gate

```ddl
door to S4 is locked
door to S5 is closed
door to S3 is hidden
```

- La stanza sorgente è quella del blocco corrente
- `<ID>` è la stanza di destinazione
- Il parser risolve la coppia di stanze alle coordinate del passage nel `dungeon_base.json`
- Se la connessione non esiste nel dungeon: warning nel log, gate ignorato

#### Stati gate

| Stato DDL | state JSON | type JSON |
|-----------|------------|-----------|
| `open` | `open` | `door` |
| `closed` | `closed` | `door` |
| `locked` | `locked` | `door` |
| `hidden` | `hidden` | `secret` |
| `portcullis` | `closed` | `portcullis` |
| `arch` | `open` | `arch` |

---

## Semantica di merge (Livello A + B)

Se una stanza ha sia `is a <template>` che direttive `has`:

1. Il template viene applicato per primo (Livello A)
2. Gli oggetti `has` vengono aggiunti sopra, con overlap check contro il template (Livello B)

**Nota v0.3:** `has` aggiunge sempre — non sostituisce oggetti dello stesso tipo nel template (Q1 aperta).

---

## Esempio completo

```ddl
# seed: 42

dungeon "Crypt of Malachar":

    S1 is a chapel:
        door to S4 is locked
        door to S5 is closed

    S4 is a bedroom

    S2:
        has bed at against_wall_north
        has chest at corner_se

    S7:
        has demonic_pentacle at center
        door to S3 is hidden
```

---

## Differenze dalla v0.2

| v0.2 (flat) | v0.3 (block) |
|---|---|
| `S1 is a chapel` — riga autonoma | `S1 is a chapel:` — header del blocco |
| `door S1 S4 is locked` — entrambe le stanze esplicite | `door to S4 is locked` — dentro il blocco di S1 |
| Nessun raggruppamento per stanza | Tutte le direttive di una stanza sono nel suo blocco |

---

## Fuori scope v0.3

- Preprocessore italiano → inglese (futuro F3)
- `against_wall_no_door` (futuro L1)
- `adjacent_to <slot_id>` (futuro L2)
- Finestre, trappole, PNG, note DM
- Topologia dungeon → DungeonMakeLang

---

## Open questions

| # | Domanda |
|---|---------|
| Q1 | Merge A+B: `has` sostituisce oggetti dello stesso tipo nel template? (v0.3: no, aggiunge sempre) |
| Q2 | Due `has` dello stesso tipo nella stessa stanza — entrambi piazzati? (v0.3: sì, se c'è spazio) |
| Q3 | Seed per stanza o globale con derivazione? (v0.3: globale con derivazione per stanza) |
