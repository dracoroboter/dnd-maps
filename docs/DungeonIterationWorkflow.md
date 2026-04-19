# Workflow Iterativo — Miglioramento Generatore Dungeon

## Scopo

Processo strutturato per migliorare `generate-dungeon.py` iterazione per iterazione,
con doppia critica (Kiro + DM) e tracciamento esplicito dei problemi aperti/chiusi.

---

## Regole del processo

1. **Kiro genera** un nuovo dungeon con i comandi standard → produce PNG, JSON e MD.
2. **Kiro scrive una critica oggettiva** del PNG confrontandola con i criteri in `PlanMaps.md`.
3. **Kiro verifica la coerenza** tra PNG, MD e JSON:
   - Ogni stanza nel PNG ha la sua sezione nel MD?
   - Le connessioni nel JSON corrispondono a porte/corridoi visibili nel PNG?
   - Stanze senza connessioni nel JSON sono visivamente isolate nel PNG?
   - Se ci sono discrepanze, vengono segnalate esplicitamente.
4. **Il DM guarda il PNG, il MD e il JSON** e aggiunge il suo giudizio.
5. **Kiro integra** i giudizi in `PlanMaps.md`.
6. **Un problema si chiude** solo con conferma esplicita del DM.
7. **Si riparte dal punto 1.**

---

## Limiti dichiarati

- Kiro può misurare oggettivamente: numero stanze, presenza porte, proporzioni corridoi/stanze, conteggio celle.
- Kiro **non può** giudicare: "sembra un dungeon D&D", "è bello", "è giocabile". Questo è compito del DM.
- L'automazione è parziale: Kiro genera PNG + critica testuale, ma il giudizio visivo richiede che il DM guardi l'immagine.

---

## Template critica Kiro (da compilare ad ogni iterazione)

```
### Iterazione N — seed X, parametri usati

**Metriche oggettive:**
- Stanze generate: N (target: M)
- Porte interne rilevate: N
- Porta verso esterno: sì/no
- Corridoi visibili: sì/no
- Stanze speciali: entrance/boss/treasure/trap presenti/assenti
- Artefatti visivi: [elenco]

**Confronto con criteri PlanMaps.md (gap aperti):**
| criterio | stato | note |
|----------|-------|------|
| Loop | ✅/❌/⚠️ | ... |
| Ingressi multipli | ✅/❌/⚠️ | ... |
| Stanze uniche | ✅/❌/⚠️ | ... |
| Angoli corridoio | ✅/❌/⚠️ | ... |
| Stanze rettangolari | ✅/❌/⚠️ | ... |

**Problemi prioritari da risolvere:**
1. ...

**Giudizio DM:** (da compilare)
```

---

## Comandi standard per ogni iterazione

```bash
python3 tech/scripts/generate-dungeon.py \
  --seed 42 --rooms 12 --title "Test Dungeon" \
  --corridor-rows 3 --output tech/reports/dungeon_base.png

python3 tech/scripts/generate-dungeon.py \
  --seed 123 --rooms 12 --title "Test Dungeon" \
  --corridor-rows 3 --output tech/reports/dungeon_base_alt.png
```

---

## Storico iterazioni

Iterazioni 1-19 riassunte in `tech/rules/PlanMaps.md` (sezione "Storico iterazioni").

Le iterazioni future seguono il template sopra, una per sezione.
