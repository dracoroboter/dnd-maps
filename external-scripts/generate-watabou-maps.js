#!/usr/bin/env node
/**
 * generate-map.js — Genera mappe da generatori Watabou
 * Uso: node tech/scripts/generate-map.js <tipo> <output.png> [opzioni]
 *
 * Tipi:
 *   dungeon    Watabou one-page-dungeon
 *   region     Watabou Perilous Shores (mappa geografica/regionale)
 *   city       Watabou Town Generator (mappa città)
 *
 * Opzioni:
 *   --seed <n>    Seed specifico (default: casuale)
 *   --size <n>    Dimensione (default: 100 per dungeon, 800 per region/city)
 *   --player      Solo dungeon: nasconde note master e segreti
 *   --pop <n>     Solo city: popolazione (influenza dimensione città)
 *   --river       Solo city: aggiunge un fiume
 *   --coast       Solo city: città costiera
 *   --citadel     Solo city: aggiunge una cittadella
 *   --walls       Solo city: aggiunge mura
 *   --plaza       Solo city: aggiunge una piazza
 *
 * Esempi:
 *   node generate-map.js dungeon mappe/Dungeon.png --seed 42 --size 150 --player
 *   node generate-map.js region mappe/Regione.png --seed 42 --size 1000
 *   node generate-map.js city mappe/Citta.png --seed 42
 */

const { chromium } = require('playwright');
const path = require('path');

const GENERATORS = {
    dungeon: {
        url: (seed, size, opts) => {
            const p = new URLSearchParams({ seed, size });
            if (opts.player) p.set('player', 'true');
            return `https://watabou.github.io/one-page-dungeon/?${p}`;
        },
        defaultSize: 100,
        viewport: { width: 1200, height: 1200 },
    },
    region: {
        url: (seed, size) => `https://watabou.github.io/perilous-shores/?seed=${seed}&size=${size}`,
        defaultSize: 800,
        viewport: { width: 1400, height: 900 },
    },
    city: {
        url: (seed, size, opts) => {
            const p = new URLSearchParams({ seed, size });
            if (opts.pop)      p.set('pop', opts.pop);
            if (opts.river)    p.set('river', 'true');
            if (opts.coast)    p.set('coast', 'true');
            if (opts.citadel)  p.set('citadel', 'true');
            if (opts.walls)    p.set('walls', 'true');
            if (opts.plaza)    p.set('plaza', 'true');
            return `https://html-classic.itch.zone/html/12710731/bin/index.html?${p}`;
        },
        defaultSize: 800,
        viewport: { width: 1200, height: 900 },
    },
};

async function main() {
    const args = process.argv.slice(2);
    if (args.length < 2) {
        console.error('Uso: node generate-map.js <dungeon|region|city> <output.png> [--seed N] [--size N] [--player]');
        process.exit(1);
    }

    const type = args[0];
    const gen = GENERATORS[type];
    if (!gen) {
        console.error(`Tipo non valido: '${type}'. Usa: dungeon, region, city`);
        process.exit(1);
    }

    const outputPath = path.resolve(args[1]);
    const seedIdx = args.indexOf('--seed');
    const sizeIdx = args.indexOf('--size');
    const seed = seedIdx >= 0 ? args[seedIdx + 1] : Math.floor(Math.random() * 2147483647);
    const size = sizeIdx >= 0 ? args[sizeIdx + 1] : gen.defaultSize;
    const player = args.includes('--player');
    const popIdx = args.indexOf('--pop');
    const opts = {
        player,
        pop:     popIdx >= 0 ? args[popIdx + 1] : null,
        river:   args.includes('--river'),
        coast:   args.includes('--coast'),
        citadel: args.includes('--citadel'),
        walls:   args.includes('--walls'),
        plaza:   args.includes('--plaza'),
    };

    const url = gen.url(seed, size, opts);
    console.log(`Tipo:   ${type}`);
    console.log(`Seed:   ${seed}`);
    console.log(`URL:    ${url}`);
    console.log(`Output: ${outputPath}`);

    const browser = await chromium.launch();
    const page = await browser.newPage();
    await page.setViewportSize(gen.viewport);
    await page.goto(url, { waitUntil: 'networkidle' });
    await page.waitForTimeout(5000);
    await page.screenshot({ path: outputPath, clip: { x: 0, y: 0, ...gen.viewport } });
    await browser.close();

    console.log(`✓ Mappa salvata: ${outputPath}`);
    console.log(`  Seed: ${seed}`);
}

main().catch(err => {
    console.error('Errore:', err.message);
    process.exit(1);
});
