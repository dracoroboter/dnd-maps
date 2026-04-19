# Linea B — Mappe grafiche per sessioni online (Roll20)

**Stato**: idea, opzioni in valutazione
**Priorità**: media (serve per L'Anello del Conte, campagna online)
**VTT target**: Roll20

---

## Problema

Per la campagna online su Roll20 servono mappe con qualità grafica accettabile — i giocatori le vedono. Tipi di mappa necessari:

- **Dungeon / fogne** — corridoi, stanze, porte, trappole
- **Edifici** — taverne, castelli, templi, case
- **Caverne** — forme organiche, stalattiti, acqua
- **Esterni** — piazze, boschi, strade, accampamenti
- **Città** — panoramiche con quartieri e punti di interesse

Il renderer v2 attuale (`json2-to-svg.py`) produce SVG in stile "penna su carta" — funzionale ma non abbastanza buono graficamente per l'uso online dove i giocatori si aspettano mappe colorate con texture e dettagli.

## Vincoli Roll20

- **Formato**: immagine statica (PNG/JPEG), caricata come sfondo pagina
- **Griglia**: Roll20 sovrappone la sua griglia — la mappa deve allinearsi (tipicamente 70px per quadretto, o multipli)
- **Dimensioni**: max 10MB per immagine, consigliato < 5MB
- **Risoluzione**: 140px/quadretto per qualità alta, 70px/quadretto per mappe grandi
- **Layer**: sfondo (mappa), token (PG/NPC), GM (note nascoste). La mappa va nel layer sfondo.
- **Dynamic Lighting** (Plus/Pro): richiede tracciare muri manualmente in Roll20, oppure importare da formato compatibile (API script)

## Opzioni valutate

### B1 — Migliorare i renderer SVG esistenti

Portare `json-to-svg-oldschool.py` o `json2-to-svg.py` a qualità "pubblicabile" aggiungendo:
- Tileset di qualità (Forgotten Adventures, 2-Minute Tabletop — gratuiti per uso personale)
- Texture per pavimenti e muri
- Ombre e illuminazione base
- Oggetti dettagliati (letti, tavoli, barili, etc.)

**Pro**: tutto in-house, controllo totale, pipeline automatizzabile
**Contro**: effort enorme per raggiungere qualità competitiva. I renderer attuali sono pensati per schemi, non per mappe illustrate. Richiederebbe riscrivere il rendering quasi da zero.

**Verdetto**: troppo costoso per il risultato. I renderer esistenti restano utili per schemi DM e prototipi, non per output giocatore.

### B2 — Tool manuali esterni

Usare Dungeondraft, Inkarnate, o simili per creare mappe manualmente.

**Pro**: risultato grafico eccellente, workflow collaudato dalla community
**Contro**: lavoro manuale per ogni mappa, nessuna automazione, software a pagamento (Dungeondraft ~$20 una tantum, Inkarnate ~$5/mese)

**Verdetto**: fallback valido ma non scala. Accettabile per mappe chiave (boss fight, location importanti), non per ogni stanza.

### B3 — Pipeline ibrida: sorgente nostro → rendering esterno

Usare il formato JSON/sorgente del progetto come **fonte di verità**, poi esportare in un formato che un tool esterno sa renderizzare.

#### B3a — Export per Dungeondraft (.dungeondraft_map)

Dungeondraft ha un formato file documentato dalla community. Si potrebbe generare un file `.dungeondraft_map` dal nostro JSON, aprirlo in Dungeondraft per ritocchi manuali, poi esportare PNG per Roll20.

**Pro**: qualità Dungeondraft, layout automatico, ritocchi manuali possibili
**Contro**: formato non ufficialmente documentato (reverse-engineered), Dungeondraft richiesto per il rendering

#### B3b — Export Universal VTT (.uvtt)

Formato aperto creato da Dungeondraft, supportato da Roll20 (con API), Foundry VTT, e altri. Contiene: immagine mappa + dati muri/porte per dynamic lighting.

```
nostro JSON → script export → .uvtt → Roll20 (con API module)
```

**Pro**: formato aperto, include dati lighting, supportato da più VTT
**Contro**: richiede comunque un'immagine di qualità come base (il formato trasporta l'immagine, non la genera)

#### B3c — Export SVG migliorato con asset pack

Usare il nostro renderer SVG ma con asset grafici di qualità:
- [Forgotten Adventures](https://www.forgotten-adventures.net/) — asset gratuiti per uso personale, PNG ad alta risoluzione
- [2-Minute Tabletop](https://2minutetabletop.com/) — asset gratuiti, stile acquerello
- Tileset custom (pixel art, painted, etc.)

Il renderer comporrebbe la mappa posizionando asset pre-disegnati su un canvas, invece di disegnare forme geometriche.

```
nostro JSON → asset-renderer.py → PNG (composizione asset) → Roll20
```

**Pro**: tutto in-house, qualità dipende dagli asset (che sono buoni), automatizzabile
**Contro**: serve un nuovo renderer (composizione tile-based), gestione asset pack, allineamento griglia

### B4 — AI image generation

Usare un modello generativo (Stable Diffusion, DALL-E, etc.) con il nostro JSON come vincolo di layout.

**Pro**: varietà infinita di stili, qualità potenzialmente alta
**Contro**: incoerenza tra generazioni, quadrettatura imprecisa, non affidabile per mappe tattiche, richiede GPU o API a pagamento

**Verdetto**: non maturo per mappe tattiche. Potenzialmente utile per mappe panoramiche (città, regioni) dove la precisione al quadretto non serve.

---

## Raccomandazione

### Strategia a due livelli

**Mappe tattiche** (dungeon, edifici, caverne — usate in combattimento):
→ **B3c** (renderer con asset pack) come obiettivo principale. È l'unica opzione che combina automazione + qualità + controllo. Il renderer esistente fornisce il layout, gli asset pack forniscono la grafica.

**Mappe panoramiche** (città, regioni, boschi — usate per esplorazione):
→ **B2** (Watabou per città, tool manuali per il resto) + **B4** (AI per illustrazioni atmosferiche) come complemento.

**Mappe chiave** (boss fight, location memorabili):
→ **B2** (Dungeondraft manuale) per le poche mappe che meritano il lavoro extra.

### Pipeline target

```
mappa.json (v2)
    │
    ├──→ mapsheet-to-dm.py  →  MappaDM.md        (Linea A, sessioni dal vivo)
    │
    ├──→ asset-renderer.py  →  mappa.png          (Linea B, Roll20)
    │         │
    │         └── asset pack (Forgotten Adventures / custom)
    │
    └──→ json2-to-svg.py    →  mappa.svg          (schema DM, prototipo)
```

Un sorgente, tre output.

## Fasi di implementazione

| fase | cosa | output |
|------|------|--------|
| 0 | Ricerca asset pack compatibili con uso personale | Lista asset, licenze, formati |
| 1 | Prototipo renderer tile-based | Script che compone PNG da asset + JSON v2 |
| 2 | Allineamento griglia Roll20 | Output a 70px/qd o 140px/qd |
| 3 | Supporto tipi di terreno | Pavimento, erba, terra, acqua, pietra |
| 4 | Oggetti e arredamento | Letti, tavoli, barili, etc. da asset pack |
| 5 | Export con metadati Roll20 | Dimensioni griglia, note per l'upload |
| 6 | (opzionale) Export .uvtt | Muri + porte per dynamic lighting |

## Domande aperte

- Forgotten Adventures richiede attribuzione? Verificare licenza per uso personale non commerciale.
- Roll20 ha limiti sul numero di pagine/mappe per campagna nel tier gratuito?
- Serve supportare dynamic lighting o basta la mappa statica come sfondo?
- Il renderer tile-based dovrebbe essere un'evoluzione di `json2-to-svg.py` (aggiungendo output PNG) o uno script separato?
- Valutare se Dungeondraft ($20 una tantum) vale l'investimento come fallback per mappe chiave.
