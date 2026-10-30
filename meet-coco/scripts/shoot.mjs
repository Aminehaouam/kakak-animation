// Screenshots of the story at chosen moments, on desktop and phone viewports, plus every console
// error and warning. Needs Playwright with Chromium and a running server (npm run dev / preview).
//
//   node scripts/shoot.mjs [--url http://127.0.0.1:5173] [--out shots] [--only 4,5] [--reduced]
//                          [--at 4:2.5,4:9]  (scene:seconds pairs instead of the default moments)
import { mkdirSync } from 'node:fs';
import { join } from 'node:path';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const { chromium } = require('playwright');

const args = Object.fromEntries(
  process.argv.slice(2).reduce((acc, a, i, all) => {
    if (a.startsWith('--')) acc.push([a.slice(2), all[i + 1] && !all[i + 1].startsWith('--') ? all[i + 1] : '1']);
    return acc;
  }, []),
);
const url = args.url || 'http://127.0.0.1:5173';
const out = args.out || 'shots';
const reduced = args.reduced === '1';
mkdirSync(out, { recursive: true });

// two or three moments per scene that show its key beats
const DEFAULT = {
  1: [0.5, 3.2, 7.5],
  2: [2.2, 3.6, 6.5],
  3: [1.5, 4.5, 8],
  4: [1.6, 4.2, 9, 15, 20],
  5: [1.0, 3.5, 7.5],
  6: [1.5, 5, 9, 13.5],
  7: [1.5, 4.3, 6.8, 9.5],
  8: [1.5, 5, 9.5],
  9: [2, 5, 8.5],
};
let moments = Object.entries(DEFAULT).flatMap(([s, ts]) => ts.map((t) => [Number(s), t]));
if (args.at) moments = args.at.split(',').map((p) => p.split(':').map(Number));
if (args.only) {
  const only = new Set(args.only.split(',').map(Number));
  moments = moments.filter(([s]) => only.has(s));
}
const viewports = (args.viewports || 'desktop,mobile').split(',');
const SIZES = { desktop: { width: 1440, height: 900 }, mobile: { width: 390, height: 844 }, tablet: { width: 1024, height: 1366 } };

const browser = await chromium.launch();
const problems = [];
for (const vp of viewports) {
  const page = await browser.newPage({ viewport: SIZES[vp], deviceScaleFactor: vp === 'mobile' ? 2 : 1, reducedMotion: reduced ? 'reduce' : 'no-preference' });
  page.on('console', (m) => (m.type() === 'error' || m.type() === 'warning') && problems.push(`[${vp}] ${m.type()}: ${m.text()}`));
  page.on('pageerror', (e) => problems.push(`[${vp}] pageerror: ${e.message}`));
  await page.goto(`${url}/?pause=1${reduced ? '&reduced=1' : ''}`);
  await page.waitForFunction(() => window.__story);
  for (const [scene, t] of moments) {
    // play into the moment from a little before, so Rive's state machine has settled
    await page.evaluate(([s, at]) => window.__story.go(s - 1, Math.max(at - 1.2, 0)), [scene, t]);
    await page.evaluate(() => window.__story.play());
    await page.waitForTimeout(1200);
    await page.evaluate(([s, at]) => { window.__story.pause(); window.__story.go(s - 1, at); }, [scene, t]);
    await page.waitForTimeout(450);
    const file = join(out, `${vp}-s${scene}-${String(t).replace('.', '_')}.png`);
    await page.screenshot({ path: file });
    console.log(file);
  }
  await page.close();
}
await browser.close();
if (problems.length) {
  console.log(`\n${problems.length} console problems:\n` + [...new Set(problems)].join('\n'));
  process.exitCode = 1;
} else {
  console.log('\nno console errors or warnings');
}
