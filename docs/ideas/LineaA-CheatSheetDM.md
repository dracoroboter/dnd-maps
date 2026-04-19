# Linea A — Cheat Sheet DM per sessioni dal vivo

**Stato**: idea, da implementare
**Priorità**: alta (serve per le prossime sessioni)
**Primo caso d'uso**: FuoriDaHellfire (MappaDM.md scritte a mano come prototipo)

---

## Problema

Nelle sessioni dal vivo il DM disegna la mappa al tavolo davanti ai giocatori. Non serve una mappa bella — serve un **riferimento rapido** da tenere dietro lo schermo con:

- Layout delle stanze e connessioni
- Dimensioni in quadretti (per disegnare proporzionato)
- Posizioni di nemici, trappole, oggetti, uscite
- Note su cosa rivelare e quando

Scrivere queste schede a mano funziona (vedi `adventures/FuoriDaHellfire/*/mappe/MappaDM.md` in dnd-generator) ma non scala: ogni mappa richiede 30-60 minuti di lavoro manuale per definire misure, disegnare ASCII, organizzare le informazioni.

## Soluzione proposta

### 1. Formato sorgente leggero (.mapsheet)

Un mini-linguaggio per descrivere una mappa in modo compatto. Ispirato a DDL/RTL ma più semplice — non descrive arredamento, descrive **layout e contenuto per il DM**.

```
# Discesa nelle Fogne
scale: 1qd = 1.5m

galleria_ingresso: tunnel 6x2
  light: "dalla grata, primi 2qd"
  trap @4qd: "filo+dardi" trigger=Percezione:12 disarm=Destrezza:12 damage=1d6
  mark: "chiave di violino (Korex)" wall=est

bivio: T from galleria_ingresso
  nord: tunnel 2x4 dead_end "allagato, acqua al ginocchio"
    clue: "impronte FALSE" check=Sopravvivenza:13
  sud: tunnel 2x3 dead_end "macerie"
  est -> nido: tunnel 4x2
    clue: "tracce vere, meno evidenti"

nido: sala 4x4
  note: "soffitto basso → svantaggio armi a due mani"
  enemy: 6x "ratto corrotto" hp=7 ac=12 atk="+4 1d4+2"
  enemy: 1x "sciame di ratti" hp=24 ac=10 atk="+2 2d6"
  alert_if: "trappola attivata → niente sorpresa"

nido -> soglia: tunnel 5x2 widens_to=3
  transition: "mattoni → pietra antica"

soglia: sala 3x3
  lore: "bassorilievi erosi" check=Storia:15
  exit -> modulo_02
```

Principi:
- **Leggibile senza tool** — il sorgente stesso è già un appunto utile
- **Struttura a blocchi indentati** — coerente con DDL
- **Keywords inglesi, contenuto italiano** — coerente con il resto del progetto
- **Nessuna coordinata** — solo dimensioni, connessioni, e posizioni relative

### 2. Script generatore (mapsheet-to-dm.py)

Prende un file `.mapsheet` e produce un `MappaDM.md` formattato con:

1. **Layout ASCII** — generato automaticamente dalle dimensioni e connessioni
2. **Tabella misure** — tutte le zone con dimensioni in qd
3. **Posizioni chiave** — sezione per sezione, cosa c'è dove
4. **Note per il disegno al volo** — ordine di rivelazione, suggerimenti grafici

```
python3 tools/mapsheet-to-dm.py avventura.mapsheet --output MappaDM.md
```

### 3. Opzionale futuro: renderer schematico

Dallo stesso sorgente `.mapsheet`, genera un PNG/SVG minimale — non per i giocatori, ma come riferimento visivo stampabile per il DM. Tipo flowchart con box e frecce, dimensioni proporzionate.

```
python3 tools/mapsheet-to-png.py avventura.mapsheet --output schema.png
```

## Fasi di implementazione

| fase | cosa | output |
|------|------|--------|
| 0 | ✅ Prototipo manuale (FuoriDaHellfire) | MappaDM.md scritti a mano |
| 1 | Definire grammatica `.mapsheet` | Specifica in `docs/` |
| 2 | Parser `.mapsheet` | Script Python |
| 3 | Generatore layout ASCII | Algoritmo di posizionamento box |
| 4 | Generatore `MappaDM.md` completo | `mapsheet-to-dm.py` |
| 5 | (opzionale) Renderer schematico PNG | `mapsheet-to-png.py` |

## Relazione con il resto del progetto

- Il formato `.mapsheet` è **indipendente** da DDL/RTL — descrive layout, non arredamento
- Potrebbe in futuro **alimentare** DDL: dal `.mapsheet` si potrebbe generare uno scheletro `.ddl` con le stanze già definite
- Il layout ASCII generato potrebbe essere riusato come base per il formato JSON v2 (mappe scritte a mano)

## Domande aperte

- Il formato deve supportare mappe non-lineari (grafi con cicli)? Per ora le avventure sono lineari, ma in futuro potrebbe servire.
- Servono livelli multipli (piano terra + sotterraneo)?
- Il generatore ASCII deve gestire mappe grandi (>30 zone) o basta un layout semplice?
