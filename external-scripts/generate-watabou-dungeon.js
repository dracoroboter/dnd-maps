#!/usr/bin/env node
/**
 * generate-dungeon-map.js — Genera una mappa dungeon da Watabou one-page-dungeon
 * Uso: node tech/scripts/generate-dungeon-map.js <output.png> [opzioni]
 *
 * Opzioni:
 *   --seed <n>      Seed specifico (default: casuale)
 *   --size <n>      Dimensione dungeon, default 100 (più alto = più stanze)
 *   --player        Modalità player: nasconde note master e segreti
 *
 * Esempi:
 *   node generate-dungeon-map.js mappe/Dungeon.png
 *   node generate-dungeon-map.js mappe/Dungeon.png --seed 42 --size 200 --player
 */

const { chromium } = require('playwright');
const path = require('path');

async function main() {
    const args = process.argv.slice(2);
    if (args.length < 1 || args[0].startsWith('--')) {
        console.error('Uso: node generate-dungeon-map.js <output.png> [--seed N] [--size N] [--player]');
        process.exit(1);
    }

    const outputPath = path.resolve(args[0]);
    const seedIdx = args.indexOf('--seed');
    const sizeIdx = args.indexOf('--size');
    const seed = seedIdx >= 0 ? args[seedIdx + 1] : Math.floor(Math.random() * 2147483647);
    const size = sizeIdx >= 0 ? args[sizeIdx + 1] : 100;
    const player = args.includes('--player');

    const params = new URLSearchParams({ seed, size });
    if (player) params.set('player', 'true');
    const url = `https://watabou.github.io/one-page-dungeon/?${params}`;

    console.log(`Seed:   ${seed}`);
    console.log(`Size:   ${size}`);
    console.log(`Modo:   ${player ? 'player (senza note master)' : 'master (con note master)'}`);
    console.log(`URL:    ${url}`);
    console.log(`Output: ${outputPath}`);

    const browser = await chromium.launch();
    const page = await browser.newPage();
    await page.setViewportSize({ width: 1200, height: 1200 });
    await page.goto(url, { waitUntil: 'networkidle' });
    await page.waitForTimeout(4000);
    await page.screenshot({ path: outputPath, clip: { x: 0, y: 0, width: 1200, height: 1200 } });
    await browser.close();

    console.log(`✓ Mappa salvata: ${outputPath}`);
    console.log(`  Seed da conservare nel file del modulo: ${seed}`);
}

main().catch(err => {
    console.error('Errore:', err.message);
    process.exit(1);
});
