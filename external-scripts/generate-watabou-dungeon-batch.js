#!/usr/bin/env node
/**
 * generate-dungeon-batch.js — Genera N mappe dungeon con seed casuali
 * Uso: node tech/scripts/generate-dungeon-batch.js <output-dir> [opzioni]
 *
 * Opzioni:
 *   --count <n>   Numero di mappe da generare (default: 5)
 *   --size <n>    Dimensione dungeon (default: 100)
 *   --player      Modalità player: nasconde note master e segreti
 *
 * Esempio:
 *   node generate-dungeon-batch.js /tmp/mappe --count 6 --size 150 --player
 *
 * Output:
 *   <output-dir>/dungeon_01.png ... dungeon_N.png
 *   <output-dir>/seeds.txt  (seed usati, da conservare nel file del modulo)
 */

const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

async function generateOne(browser, seed, size, player, outputPath) {
    const params = new URLSearchParams({ seed, size });
    if (player) params.set('player', 'true');
    const url = `https://watabou.github.io/one-page-dungeon/?${params}`;

    const page = await browser.newPage();
    await page.setViewportSize({ width: 1200, height: 1200 });
    await page.goto(url, { waitUntil: 'networkidle' });
    await page.waitForTimeout(4000);
    await page.screenshot({ path: outputPath, clip: { x: 0, y: 0, width: 1200, height: 1200 } });
    await page.close();
    return url;
}

async function main() {
    const args = process.argv.slice(2);
    if (args.length < 1 || args[0].startsWith('--')) {
        console.error('Uso: node generate-dungeon-batch.js <output-dir> [--count N] [--size N] [--player]');
        process.exit(1);
    }

    const outputDir = path.resolve(args[0]);
    const countIdx = args.indexOf('--count');
    const sizeIdx = args.indexOf('--size');
    const count = countIdx >= 0 ? parseInt(args[countIdx + 1]) : 5;
    const size = sizeIdx >= 0 ? args[sizeIdx + 1] : 100;
    const player = args.includes('--player');

    fs.mkdirSync(outputDir, { recursive: true });

    console.log(`=== Generazione ${count} mappe (size=${size}, ${player ? 'player' : 'master'}) ===\n`);

    const browser = await chromium.launch();
    const seeds = [];

    for (let i = 1; i <= count; i++) {
        const seed = Math.floor(Math.random() * 2147483647);
        const filename = `dungeon_${String(i).padStart(2, '0')}.png`;
        const outputPath = path.join(outputDir, filename);
        process.stdout.write(`  [${i}/${count}] seed=${seed} → ${filename} ... `);
        await generateOne(browser, seed, size, player, outputPath);
        seeds.push({ file: filename, seed, url: `https://watabou.github.io/one-page-dungeon/?seed=${seed}&size=${size}${player ? '&player=true' : ''}` });
        console.log('✓');
    }

    await browser.close();

    // Salva seeds.txt
    const seedsPath = path.join(outputDir, 'seeds.txt');
    const seedsContent = seeds.map(s => `${s.file}\tseed=${s.seed}\t${s.url}`).join('\n') + '\n';
    fs.writeFileSync(seedsPath, seedsContent);

    console.log(`\n✓ ${count} mappe salvate in: ${outputDir}`);
    console.log(`  seeds.txt: conserva il seed della mappa scelta nel file del modulo`);
}

main().catch(err => {
    console.error('Errore:', err.message);
    process.exit(1);
});
