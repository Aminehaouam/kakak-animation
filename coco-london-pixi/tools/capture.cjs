// Renders the experiment in headless Chromium (Playwright): a still at any moment and size, each
// layer on its own, or the frames of a video. Needs a server: npm run build && npm run preview.
//
//   node tools/capture.cjs still  --t 12 --size 3840x2160 --out renders/london-4k.png
//   node tools/capture.cjs layers --t 12 --size 1920x1080 --out renders/layers
//   node tools/capture.cjs video  --from 0 --to 20 --fps 30 --size 1920x1080 --out renders/frames
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const [mode = 'still', ...rest] = process.argv.slice(2);
const opt = {};
for (let i = 0; i < rest.length; i += 2) opt[rest[i].replace(/^--/, '')] = rest[i + 1];
const url = opt.url || 'http://127.0.0.1:4180/';
const [w, h] = (opt.size || '1920x1080').split('x').map(Number);
const out = opt.out || 'renders/still.png';

(async () => {
  const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const page = await browser.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: 1 });
  const problems = [];
  page.on('console', (m) => (m.type() === 'error' || m.type() === 'warning') && problems.push(`${m.type()}: ${m.text()}`));
  page.on('pageerror', (e) => problems.push(`pageerror: ${e.message}`));
  await page.goto(`${url}?capture&t=${opt.t || 0}`);
  await page.waitForFunction(() => window.__scene && window.__scene.ready, null, { timeout: 120000 });
  await page.evaluate(() => window.__scene.pause());
  const shot = async (file, t) => {
    await page.evaluate((tt) => window.__scene.setTime(tt), t);
    await page.screenshot({ path: file });
  };
  if (mode === 'still') {
    fs.mkdirSync(path.dirname(out), { recursive: true });
    await shot(out, Number(opt.t || 12));
    console.log(out);
  } else if (mode === 'layers') {
    fs.mkdirSync(out, { recursive: true });
    const names = await page.evaluate(() => window.__scene.layers());
    const t = Number(opt.t || 12);
    for (const n of names) {
      await page.evaluate((nn) => window.__scene.show([nn]), n);
      await shot(path.join(out, `${n}.png`), t);
    }
    await page.evaluate(() => window.__scene.show(null));
    console.log(names.join(', '));
  } else if (mode === 'video') {
    fs.mkdirSync(out, { recursive: true });
    const fps = Number(opt.fps || 30);
    const from = Number(opt.from || 0);
    const to = Number(opt.to || 20);
    let i = 0;
    for (let t = from; t < to - 1e-6; t += 1 / fps) {
      await shot(path.join(out, `f${String(i).padStart(5, '0')}.png`), t);
      i++;
    }
    console.log(`${i} frames`);
  }
  console.log(problems.length ? problems.join('\n') : 'no console errors or warnings');
  await browser.close();
})();
