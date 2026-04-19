# Reverse Engineering: json-to-svg-oldschool.py

Analisi del renderer SVG oldschool esistente per identificare tecniche e codice riusabile nel renderer v2.

## Tecniche grafiche

### 1. Hatching randomizzato (effetto "penna a mano")
- Funzione `hatch_lines(cx, cy, tile, rng, density, ext)`
- Linee diagonali con angolo 40-60° e lunghezza variabile (25-60% del tile)
- Densità diversa per muri interni (20) ed esterni (14)
- Opacità diversa: 0.85 interni, 0.5 esterni
- Usa `random.Random(seed)` per risultati riproducibili
- **DA PORTARE**: sostituisce il tratteggio uniforme del renderer v2

### 2. Griglia pavimento
- Quadretti sottili (`stroke="#ccc" stroke-width="0.4"`) dentro le stanze
- Solo sulle celle FLOOR/CORR, non sui muri
- **DA PORTARE**: la griglia v2 copre tutto, dovrebbe coprire solo le aree

### 3. Bordi muro
- Calcolati cella per cella: per ogni cella pavimento, controlla i 4 vicini
- Se il vicino è muro → disegna linea nera sul bordo condiviso
- Spessore: `max(1.5, tile * 0.12)`
- Questo crea aperture naturali dove ci sono porte/passaggi
- **DA PORTARE**: nel v2 i bordi sono del rettangolo intero, non permettono aperture

### 4. Sistema gate (porte) a plugin
- File: `tech/templates/gates/gate_oldschool.py`
- Caricato dinamicamente con `importlib`
- Funzione `render_gate(gate, orient, x, y, w, h, tile, sw, lines)`
- Tipi: door (open/closed/locked), portcullis, arch, secret (hidden/found)
- Ogni tipo ha rendering diverso (arco per porta aperta, linea per chiusa, ecc.)
- **DA PORTARE**: il v2 disegna porte come rettangolini, dovrebbe usare i plugin

### 5. Sistema oggetti a plugin
- Template JSON in `tech/templates/objects/` (es. `bed.json`, `chest.json`, `altar.json`)
- Renderer Python per stile in `tech/templates/objects/` (es. `bed_oldschool.py`)
- Template definisce: size, directional, directional_axis
- Renderer disegna l'oggetto in SVG dato posizione e dimensioni
- Overlap check: oggetti non si sovrappongono (tranne `allow_overlap: true`)
- **DA PORTARE**: il canale d'acqua delle fogne potrebbe essere un oggetto "water_channel"

### 6. Enrichment separato
- File `dungeon_enrichment.json` con gates, windows, objects
- Caricato e mergiato nel data dict come `_enrichment`
- Validato da `validate_enrichment()` contro il dungeon base
- **DA VALUTARE**: nel v2 gli oggetti sono nel JSON principale. Potremmo supportare entrambi.

### 7. Header/Footer
- Titolo centrato: `text-anchor="middle"`, font Georgia serif, size 20, bold
- Sotto: copyright, anno, CC BY, font sans-serif size 9
- View label [DM]/[Players] accanto al titolo
- **DA PORTARE**: il v2 ha il titolo a sinistra e piccolo

## File coinvolti

| file | ruolo |
|------|-------|
| `tech/scripts/json-to-svg-oldschool.py` | Renderer principale |
| `tech/scripts/dungeon_svg_core.py` | Modulo condiviso: load, grid, passages, bounding box |
| `tech/templates/gates/gate_oldschool.py` | Plugin rendering porte |
| `tech/templates/objects/*.json` | Template oggetti (size, directional) |
| `tech/templates/objects/*_oldschool.py` | Plugin rendering oggetti per stile |

## Differenze strutturali v1 vs v2

| aspetto | v1 (oldschool) | v2 (nuovo) |
|---------|---------------|------------|
| Input | griglia celle (FLOOR/WALL/CORR) | aree geometriche (rect/circle/poly) |
| Muri | celle WALL con hatching | spazio tra aree con hatching |
| Porte | celle passage nella griglia | connessioni esplicite nel JSON |
| Oggetti | enrichment JSON separato | nel JSON principale (+ enrichment opzionale) |
| Forme | solo rettangoli | rettangoli, cerchi, poligoni |

## Piano per il renderer v2

1. Portare `hatch_lines()` con seed per riproducibilità
2. Disegnare hatching su tutto lo sfondo, poi stanze bianche sopra (come ora ma con hatching random)
3. Connessioni: disegnare corridoi bianchi tra le aree, con bordi neri sui lati lunghi e aperture alle estremità
4. Porte: usare il plugin gate_oldschool o riscrivere rendering simile
5. Header centrato con font grande
6. Oggetti: supportare plugin come v1, con canale d'acqua come nuovo tipo
