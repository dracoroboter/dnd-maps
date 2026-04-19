# Maps.md — Documentazione Tool e Script per Mappe

## Script disponibili

### `generate-watabou-dungeon.js`
Genera una singola mappa dungeon da Watabou one-page-dungeon.

```bash
node tech/scripts/generate-watabou-dungeon.js <output.png> [--seed N] [--size N] [--player]
```

- `--seed N` — seed specifico (default: casuale)
- `--size N` — dimensione dungeon, default 100 (valori più alti = più stanze, ~150-200 per dungeon grandi)
- `--player` — nasconde note master e segreti (per versione da mostrare ai giocatori)

Conservare il seed nel file del modulo per poter rigenerare la stessa mappa.

---

### `generate-watabou-dungeon-batch.js`
Genera N mappe dungeon con seed casuali e salva un file `seeds.txt`.

```bash
node tech/scripts/generate-watabou-dungeon-batch.js <output-dir> [--count N] [--size N] [--player]
```

- `--count N` — numero di mappe (default: 5)
- `--size N` — dimensione dungeon (default: 100)
- `--player` — modalità player

Output: `dungeon_01.png` ... `dungeon_N.png` + `seeds.txt` con seed e URL di ogni mappa.

---

### `generate-watabou-maps.js`
Script unificato per dungeon, mappe regionali (Perilous Shores) e città (Town Generator).

```bash
node tech/scripts/generate-watabou-maps.js <tipo> <output.png> [opzioni]
```

**Tipi:**
- `dungeon` — Watabou one-page-dungeon
- `region` — Watabou Perilous Shores ⚠ stile non gradito, uso sconsigliato
- `city` — Watabou Town Generator

**Opzioni dungeon:** `--seed`, `--size`, `--player`

**Opzioni city:** `--seed`, `--size`, `--pop N`, `--river`, `--coast`, `--citadel`, `--walls`, `--plaza`

---

## Tool manuali (nessuna API)

| tool | uso | URL |
|------|-----|-----|
| Inkarnate | Mappe geografiche/regionali custom | https://inkarnate.com |
| DungeonFog | Battle map dettagliate | https://app.dungeonfog.com |
| DungeonScrawl | Dungeon con stile diverso | https://app.dungeonscrawl.com |

---

## Valutazioni tool scartati

**Watabou Perilous Shores** — stile non gradito per mappe regionali di avventura. Script disponibile ma uso sconsigliato.

**Azgaar's Fantasy Map Generator** — mappe troppo ampie e con pochi dettagli per essere utili a livello di avventura. Adatto per worldbuilding su scala continentale, non per singole avventure.

**donjon.bin.sh** — genera dungeon lato client in JS, nessun endpoint REST diretto. Richiederebbe Playwright come Watabou — non esplorato ulteriormente.

---

## Workflow consigliato

### Mappa dungeon
1. `node tech/scripts/generate-watabou-dungeon-batch.js /tmp/mappe --count 6 --size 150 --player`
2. Aprire i PNG, scegliere quello più adatto
3. Copiare il PNG scelto in `NN_NomeModulo/mappe/`
4. Annotare il seed nel file del modulo (sezione `## Note al master` o commento)

### Mappa città
1. `node tech/scripts/generate-watabou-maps.js city /tmp/citta.png --seed 42 --walls --river`
2. Verificare il risultato, cambiare seed se necessario
3. Copiare in `mappe/`

### Mappa geografica/regionale
Nessuno strumento automatizzabile con stile soddisfacente. Usare Inkarnate manualmente.
