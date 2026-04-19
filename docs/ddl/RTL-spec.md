# RoomTemplateLang (RTL) — Specifica v0.1

> Linguaggio semi-naturale per definire template di stanze riutilizzabili.
> File: `.rtl` — sorgente leggibile, compilato in `tech/templates/rooms/<nome>.json`.
> Documentazione automatica del JSON corrispondente.

---

## Relazione con DDL

| | RTL | DDL |
|---|---|---|
| **Scope** | Definisce un *archetipo* (cosa è in generale una camera da letto) | Descrive un'*istanza* (arredamento di S1 nel dungeon X) |
| **Room ID** | Assente — si applica a qualsiasi stanza | Presente — `stanza S1 ...` |
| **Coordinate** | Mai esplicite — calcolate dal placement engine | Semantiche o implicite nel template |
| **File** | `tech/templates/rooms/*.rtl` | `avventure/NomeAvventura/*.ddl` |

---

## Convenzioni notazione

Identiche a DDL:

- **`(parola)`** — filler opzionale singolo, ignorato dal parser
- **`(parola, parola)`** — filler opzionale, una tra le alternative, ignorato dal parser
- **`[parola, parola]`** — sinonimi sintattici, il parser accetta qualsiasi
- **Indentazione** — 4 spazi, definisce la struttura
- **`:`** — separatore sintattico (chiude un'intestazione o introduce una lista)
- **Case** — case-insensitive
- **Commenti** — righe che iniziano con `#`

---

## Struttura generale

```
(Il) template (per la, per il, per) "nome" (è così definito:)
    [Grandezza minima, min]: LxA

    <slot>
    <slot>
    ...

    (esistono dei) vincoli: <lista vincoli>
    todo: <lista vincoli futuri>
```

---

## Intestazione template

```
template "camera da letto":
template "cappella":
(Il) template (per la) "stanza dei tesori" (è così definito:)
```

- Il nome tra virgolette è l'identificatore — deve corrispondere all'`id` nel JSON
- `ddl_aliases` nel JSON elenca i termini DDL che attivano questo template

---

## Dimensione minima

```
[Grandezza minima, min]: 3×3
[Grandezza minima, min]: 4x6
```

- Formato: `LxA` o `L×A` (larghezza × altezza in quadretti)
- Se la stanza è più piccola: warning nel log + proposta di modifica minima

---

## Slot (righe oggetto)

```
<tipo>  <obbligatorio|opzionale>  <conteggio>  [strategia]  (<filler>): <lista posizioni>
```

### Tipo

Parola singola o composta che identifica l'oggetto:

```
letto
forziere
tavolo grande
colonna
```

Deve corrispondere al campo `type` in `tech/templates/objects/<tipo>.json`.

### Obbligatorietà

```
obbligatorio     ← required: true nel JSON
opzionale        ← required: false nel JSON
```

Se un oggetto `obbligatorio` non può essere piazzato: warning + proposta minima.
Se un oggetto `opzionale` non può essere piazzato: warning silenzioso.

### Conteggio

**Intervallo con fill** (piazza quanti ne entrano, min-max):

```
da 1 a 2  [da mettere, riempi]
da 1 a 4  riempi
```

**Collegato a un altro slot** (ratio):

```
1 per letto
2 per altare
1 per letto
```

Il conteggio viene calcolato sul numero di oggetti *effettivamente piazzati* dello slot di riferimento.

### Lista posizioni

Dopo `:` — una o più posizioni in ordine di preferenza, separate da virgola.
Il placement engine le prova nell'ordine indicato (con shuffling seed per quelle equivalenti).

```
: contro il muro
: contro il muro nord
: angolo, contro il muro
: al centro, contro il muro est, angolo
```

#### Posizioni disponibili

| RTL | Significato | Nota |
|-----|-------------|------|
| `al centro` | Centro geometrico della stanza | |
| `contro il muro` | Qualsiasi muro — seed sceglie quale | Any wall |
| `contro il muro nord` | Muro nord, centrato | |
| `contro il muro sud` | Muro sud, centrato | |
| `contro il muro est` | Muro est, centrato | |
| `contro il muro ovest` | Muro ovest, centrato | |
| `angolo` | Qualsiasi angolo — seed sceglie quale | Any corner |
| `nell'angolo nord-est` | Angolo nord-est | |
| `nell'angolo nord-ovest` | Angolo nord-ovest | |
| `nell'angolo sud-est` | Angolo sud-est | |
| `nell'angolo sud-ovest` | Angolo sud-ovest | |

Per oggetti direzionali (es. letto) la direzione è dedotta automaticamente dal muro scelto.

---

## Vincoli

```
(esistono dei) vincoli: <lista>
todo: <lista>
```

| Identificatore | Descrizione | Stato |
|----------------|-------------|-------|
| `no_overlap` | Gli oggetti non si sovrappongono | Implementato |
| `clearance_porte` | Nessun oggetto blocca il passaggio delle porte | Todo |

---

## Esempio completo

```rtl
# Camera da letto standard — v0.1

(Il) template (per la) "camera da letto" (è così definito:)
    [Grandezza minima, min]: 3×3

    (Un) letto  (è)  obbligatorio  da 1 a 2  [da mettere, riempi]  (la posizione sarà): contro il muro
    (Il, La) forziere  (è)  opzionale  (ne esistono)  1 per letto  (uno tra): angolo, contro il muro

    (esistono dei) vincoli: no_overlap
    todo: clearance_porte
```

JSON equivalente generato: `tech/templates/rooms/bedroom.json`

---

## Fuori scope v0.1

- Oggetti con posizioni relative ad altri oggetti (es. "comodino accanto al letto")
- Condizioni basate sul tipo di stanza (es. "se h > 6 aggiungi un secondo letto")
- Stanze con forme non rettangolari
