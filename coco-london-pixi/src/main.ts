import { Application, TextureSource } from 'pixi.js';
import { loadLibrary } from './scene/assets';
import { H, LondonScene, W } from './scene/build';
import './style.css';

// ?t=12 shows that moment, paused; ?speed=0.5 slows time; ?capture keeps the drawing buffer for screenshots
const params = new URLSearchParams(location.search);
const fixedT = params.has('t') ? Number(params.get('t')) : null;
const speed = Number(params.get('speed') ?? 1);

async function boot() {
  // the artwork is painted for a 4K frame and usually shown smaller: mipmaps keep it crisp
  TextureSource.defaultOptions.autoGenerateMipmaps = true;
  TextureSource.defaultOptions.scaleMode = 'linear';
  const app = new Application();
  await app.init({
    resizeTo: window,
    background: '#cfe3f1',
    antialias: true,
    resolution: Math.min(window.devicePixelRatio || 1, 2),
    autoDensity: true,
    preserveDrawingBuffer: params.has('capture'),
  });
  document.getElementById('stage')!.appendChild(app.canvas);
  const lib = await loadLibrary({ water_displace: 'art/water_displace.png', water_ripples: 'art/water_ripples.png' });
  const scene = new LondonScene(app, lib);
  app.stage.addChild(scene.world);

  // fill the screen with the 16:9 frame, cropping the edges on other shapes
  const fit = () => {
    const s = Math.max(app.screen.width / W, app.screen.height / H);
    scene.world.scale.set(s);
    scene.world.position.set((app.screen.width - W * s) / 2, (app.screen.height - H * s) / 2);
  };
  fit();
  app.renderer.on('resize', fit);
  window.addEventListener('pointermove', (e) => scene.setPointer((e.clientX / window.innerWidth) * 2 - 1));

  let t = fixedT ?? 0;
  let last = performance.now();
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (fixedT === null && reduced) t = 12; // reduced motion: show the settled scene, still
  scene.update(t);
  app.ticker.add(() => {
    const now = performance.now();
    const dt = Math.min((now - last) / 1000, 0.1);
    last = now;
    if (fixedT === null && !reduced) t += dt * speed;
    scene.update(t, dt);
  });

  // a small hook for capture scripts
  (window as unknown as { __scene: object }).__scene = {
    setTime(v: number) {
      t = v;
      scene.update(t, 0);
      app.render();
    },
    pause() {
      app.ticker.stop();
    },
    play() {
      last = performance.now();
      app.ticker.start();
    },
    layers: () => scene.layers.map((l) => l.name),
    show(names: string[] | null) {
      for (const l of scene.layers) l.node.visible = !names || names.includes(l.name);
      app.render();
    },
    ready: true,
  };
}

boot().catch((err) => {
  console.error(err);
  document.body.insertAdjacentHTML('beforeend', `<p style="font:16px system-ui;padding:24px">The scene could not start: ${String(err)}</p>`);
});
