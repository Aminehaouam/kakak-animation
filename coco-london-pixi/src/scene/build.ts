// The London scene: painted layers placed from scene.json, with light, atmosphere, water and
// motion added in PixiJS. update(t) poses everything for time t (seconds), so any moment can be
// rendered exactly, live or for a still.
import { ColorMatrixFilter, Container, Graphics, MeshPlane, Sprite, type Application } from 'pixi.js';
import type { Library } from './assets';
import { Coco } from './coco';
import { contactShadow, radial, vertical } from './fx';
import { River } from './river';
import layout from './scene.json';

export const W = layout.frame[0];
export const H = layout.frame[1];
export const MARGIN = 200;
const WIDE = W + 2 * MARGIN;
const DEG = Math.PI / 180;
const clamp = (v: number, a = 0, b = 1) => Math.min(Math.max(v, a), b);

interface Item {
  art: string;
  x: number;
  y: number;
  drift?: number;
  spin?: number;
  alpha?: number;
}

interface Layer {
  name: string;
  depth: number;
  node: Container;
}

export class LondonScene {
  /** the whole frame, 3840 x 2160 world units; the app scales it to the screen */
  readonly world = new Container();
  readonly layers: Layer[] = [];
  private clouds: Array<{ s: Sprite; item: Item }> = [];
  private wheel?: Sprite;
  private capsules: Sprite[] = [];
  private eyeAt = { x: 0, y: 0 };
  private river!: River;
  private coco!: Coco;
  private bus!: { node: Container; wheels: Sprite[]; shadow: Sprite };
  private walkers: Array<{ node: Container; shadow: Sprite; x0: number; speed: number; y: number; dir: number }> = [];
  private far = new Container();
  private cloudShadows: Array<{ s: Sprite; x0: number; speed: number; span: number }> = [];
  private gulls: Array<{ g: Graphics; x0: number; y0: number; speed: number; phase: number; size: number }> = [];
  private flag?: { mesh: MeshPlane; rest: Float32Array; w: number };
  private pointer = 0;
  private pointerTarget = 0;

  constructor(private app: Application, private lib: Library) {
    this.build();
  }

  private layer(name: string, depth: number, parent: Container = this.world) {
    const node = new Container();
    node.label = name;
    parent.addChild(node);
    this.layers.push({ name, depth, node });
    return node;
  }

  private place(item: Item) {
    const s = this.lib.sprite(item.art);
    s.position.set(item.x, item.y);
    if (item.alpha !== undefined) s.alpha = item.alpha;
    return s;
  }

  private shadowAt(parent: Container, x: number, y: number, w: number, h: number, alpha: number) {
    const s = new Sprite(contactShadow());
    s.anchor.set(0.5);
    s.position.set(x, y);
    s.width = w;
    s.height = h;
    s.alpha = alpha;
    parent.addChild(s);
    return s;
  }

  /** a soft band of haze between depth planes: strongest at the horizon */
  private fog(name: string, depth: number, alpha: number, parent: Container) {
    const node = this.layer(name, depth, parent);
    const s = new Sprite(vertical(512, [[0, 'rgba(221,236,246,0)'], [0.55, 'rgba(221,236,246,0.35)'], [0.86, 'rgba(226,239,246,1)'], [0.95, 'rgba(226,239,246,0.6)'], [1, 'rgba(226,239,246,0)']]));
    s.position.set(-MARGIN, 260);
    s.width = WIDE;
    s.height = 1222 - 260 + 30;
    s.alpha = alpha;
    node.addChild(s);
  }

  private build() {
    const L = layout.layers as Array<{ name: string; depth: number; items: Item[] }>;
    const byName = (n: string) => L.find((l) => l.name === n)!;
    const addLayer = (n: string, parent: Container = this.world) => {
      const def = byName(n);
      const node = this.layer(def.name, def.depth, parent);
      for (const it of def.items) {
        const s = this.place(it);
        node.addChild(s);
        if (it.drift) this.clouds.push({ s, item: it });
      }
      return node;
    };

    // ---- sky, sun and clouds
    addLayer('sky');
    const sun = this.layer('sunlight', 0.02);
    const glow = new Sprite(radial(512, [[0, 'rgba(255,248,226,0.95)'], [0.25, 'rgba(255,244,214,0.45)'], [0.6, 'rgba(255,240,210,0.12)'], [1, 'rgba(255,240,210,0)']]));
    glow.anchor.set(0.5);
    glow.position.set(260, -120);
    glow.width = glow.height = 2600;
    glow.blendMode = 'screen';
    sun.addChild(glow);
    addLayer('clouds-far');
    addLayer('clouds');
    // a few gulls gliding high over the river
    const birds = this.layer('gulls', 0.12);
    for (const [x0, y0, speed, size] of [[600, 640, 34, 1.0], [980, 560, 30, 0.8], [2900, 520, -26, 0.9]] as const) {
      const g = new Graphics();
      birds.addChild(g);
      this.gulls.push({ g, x0, y0, speed, phase: x0 * 0.01, size });
    }

    // ---- the far city, with haze between its depths
    addLayer('skyline-far');
    this.fog('haze-far', 0.2, 0.55, this.world);
    this.world.addChild(this.far);
    addLayer('landmarks-back', this.far);
    this.fog('haze-mid', 0.28, 0.22, this.far);
    addLayer('riverside', this.far);
    const front = addLayer('landmarks-front', this.far);
    // the Eye's wheel turns; its 32 capsules stay level
    for (const child of front.children) {
      const sp = child as Sprite;
      if (sp.texture === this.lib.tex.eye_wheel) {
        this.wheel = sp;
        this.eyeAt = { x: sp.x, y: sp.y };
        const idx = front.getChildIndex(sp);
        for (let i = 0; i < 32; i++) {
          const c = this.lib.sprite('eye_capsule');
          front.addChildAt(c, idx + 1);
          this.capsules.push(c);
        }
      }
    }
    // the Union flag on Victoria Tower, a mesh that waves in the breeze
    const wm = front.children.find((c) => (c as Sprite).texture === this.lib.tex.westminster) as Sprite | undefined;
    const fpos = this.lib.man.westminster?.flag as [number, number] | undefined;
    if (wm && fpos) {
      const mesh = new MeshPlane({ texture: this.lib.tex.flag_union, verticesX: 14, verticesY: 4 });
      mesh.position.set(wm.x + fpos[0], wm.y + fpos[1]);
      mesh.scale.set(0.5);
      front.addChild(mesh);
      this.flag = { mesh, rest: new Float32Array(mesh.geometry.positions), w: this.lib.tex.flag_union.width };
    }
    this.fog('haze-near', 0.32, 0.07, this.far);
    addLayer('farbank', this.far);
    addLayer('tower-bridge', this.far);

    // ---- the river
    const riverLayer = this.layer('river', byName('river').depth);
    this.river = new River(this.lib, { waterTop: layout.waterTop, waterBottom: layout.coping + 40, width: WIDE, margin: MARGIN, source: this.far });
    riverLayer.addChild(this.river.water, this.river.boats);
    this.river.addBoat('boat_small', { y: 1296, speed: 34, scale: 0.62, dir: 1, x0: 2100, span: 4800 });
    this.river.addBoat('boat', { y: 1446, speed: 52, scale: 0.86, dir: -1, x0: 2950, span: 5200 });

    // shadows of the clouds gliding over the water
    const water = this.river.water;
    for (const [x0, y, w, h, speed] of [[400, 1330, 1500, 150, 14], [2600, 1470, 1900, 170, 12], [3900, 1290, 1100, 110, 15]] as const) {
      const sh = new Sprite(contactShadow());
      sh.anchor.set(0.5);
      sh.width = w;
      sh.height = h;
      sh.alpha = 0.32;
      sh.blendMode = 'multiply';
      water.addChild(sh);
      this.cloudShadows.push({ s: sh, x0, speed, span: WIDE + w });
      sh.y = y;
    }

    // ---- the near embankment
    addLayer('balustrade');
    addLayer('promenade');
    const groundShade = this.layer('cloud-shade', byName('promenade').depth);
    for (const [x0, y, w, h, speed] of [[1200, 1780, 2200, 300, 13], [3600, 1900, 1800, 260, 12]] as const) {
      const sh = new Sprite(contactShadow());
      sh.anchor.set(0.5);
      sh.width = w;
      sh.height = h;
      sh.alpha = 0.22;
      sh.blendMode = 'multiply';
      sh.y = y;
      groundShade.addChild(sh);
      this.cloudShadows.push({ s: sh, x0, speed, span: WIDE + w });
    }
    const street = this.layer('street', byName('street').depth);
    const streetDef = byName('street');
    for (const it of streetDef.items) this.shadowAt(street, it.x + 10, it.y + 2, 120, 26, 0.5);
    for (const [name, x, scale] of [['tree_prom_2', -60, 1.0], ['tree_prom_1', 3930, 1.08]] as const) {
      this.shadowAt(street, x + 20, 1668, 380 * scale, 52 * scale, 0.55);
      const tr = this.lib.sprite(name);
      tr.position.set(x, 1672);
      tr.scale.set(scale);
      street.addChild(tr);
    }
    for (const it of streetDef.items) {
      const lamp = this.place(it);
      lamp.scale.set(1.14);
      street.addChild(lamp);
    }
    // people on the promenade: some standing, two strolling
    const standing: Array<[string, number, number, number]> = [['person_2', 1840, 1716, 1], ['person_6', 1876, 1720, 1], ['person_4', 2980, 1704, -1], ['person_8', 520, 1712, 1], ['person_1', 3420, 1726, -1]];
    for (const [name, x, y, dir] of standing) {
      this.shadowAt(street, x + 6, y + 2, 64, 13, 0.45);
      const p = this.lib.sprite(name);
      p.position.set(x, y);
      p.scale.set(dir, 1);
      street.addChild(p);
    }
    for (const [name, x0, speed, y, dir] of [['person_3', 300, 38, 1738, 1], ['person_7', 3600, 44, 1708, -1]] as const) {
      const shadow = this.shadowAt(street, 0, y + 2, 64, 13, 0.45);
      const node = this.lib.sprite(name);
      node.scale.set(dir, 1);
      street.addChild(node);
      this.walkers.push({ node, shadow, x0, speed, y, dir });
    }

    // ---- Coco
    const cocoLayer = this.layer('coco', 0.82);
    const perch = layout.coco.perch as [number, number];
    this.coco = new Coco(this.lib, perch, { start: 1.0, land: 6.2 });
    cocoLayer.addChild(this.coco.shadow, this.coco.root);

    // ---- traffic
    const traffic = this.layer('traffic', 0.95);
    const busNode = new Container();
    const busShadow = this.shadowAt(traffic, 0, 1978, 700, 46, 0.6);
    busNode.addChild(this.lib.sprite('bus'));
    const wheels: Sprite[] = [];
    for (const [dx, dy] of this.lib.man.bus.wheels as Array<[number, number]>) {
      const wh = this.lib.sprite('bus_wheel');
      wh.position.set(dx, dy);
      busNode.addChild(wh);
      wheels.push(wh);
    }
    traffic.addChild(busNode);
    this.bus = { node: busNode, wheels, shadow: busShadow };

    // ---- foreground framing
    const fg = this.layer('foreground', 1.18);
    for (const [name, x, y, scale] of [['bush_1', 150, 2196, 1.15], ['bush_3', 620, 2200, 1.0], ['bush_2', 3560, 2190, 1.1]] as const) {
      const b = this.lib.sprite(name);
      b.position.set(x, y);
      b.scale.set(scale);
      fg.addChild(b);
    }

    // a gentle grade: a little more colour and contrast, as a print would have
    const grade = new ColorMatrixFilter();
    grade.saturate(0.14, true);
    grade.contrast(0.06, true);
    this.world.filters = [grade];

    // ---- light over everything: a warm wash from the sun, a soft vignette
    const light = this.layer('light', 0);
    const wash = new Sprite(radial(512, [[0, 'rgba(255,236,200,0.5)'], [0.5, 'rgba(255,236,200,0.14)'], [1, 'rgba(255,236,200,0)']]));
    wash.anchor.set(0.5);
    wash.position.set(500, 120);
    wash.width = 4400;
    wash.height = 3000;
    wash.blendMode = 'screen';
    wash.alpha = 0.55;
    light.addChild(wash);
    const cool = new Sprite(radial(512, [[0, 'rgba(40,62,98,0.42)'], [0.55, 'rgba(40,62,98,0.14)'], [1, 'rgba(40,62,98,0)']]));
    cool.anchor.set(0.5);
    cool.position.set(W * 0.98, H * 1.02);
    cool.width = 3600;
    cool.height = 2200;
    cool.blendMode = 'multiply';
    cool.alpha = 0.5;
    light.addChild(cool);
    const vignette = new Sprite(radial(512, [[0, 'rgba(18,32,52,0)'], [0.62, 'rgba(18,32,52,0)'], [1, 'rgba(18,32,52,0.55)']]));
    vignette.anchor.set(0.5);
    vignette.position.set(W / 2, H / 2);
    vignette.width = W * 1.45;
    vignette.height = H * 1.6;
    vignette.blendMode = 'multiply';
    vignette.alpha = 0.6;
    light.addChild(vignette);
  }

  /** gentle pointer parallax, -1 .. 1 across the screen */
  setPointer(v: number) {
    this.pointerTarget = clamp(v, -1, 1);
  }

  update(t: number, dt = 0) {
    this.pointer += (this.pointerTarget - this.pointer) * Math.min(1, dt * 2.5);
    // the camera drifts slowly; nearer layers move more
    const camX = 46 * Math.sin((t / 48) * Math.PI * 2) + this.pointer * 70;
    for (const l of this.layers) l.node.x = -camX * l.depth;
    // the far group moves as one (its children carry their own depths)
    this.far.x = 0;
    for (const { s, item } of this.clouds) {
      const span = WIDE + 1600;
      s.x = ((((item.x + (item.drift ?? 0) * t + 800) % span) + span) % span) - 800 - MARGIN;
    }
    if (this.wheel) {
      const a = (t * 0.35 * DEG) % (Math.PI * 2);
      this.wheel.rotation = a;
      const r = 374;
      this.capsules.forEach((c, i) => {
        const ang = a + (i / 32) * Math.PI * 2;
        c.position.set(this.eyeAt.x + Math.cos(ang) * r, this.eyeAt.y + Math.sin(ang) * r);
      });
    }
    for (const c of this.cloudShadows) {
      c.s.x = ((((c.x0 + c.speed * t) % c.span) + c.span) % c.span) - c.s.width / 2 - MARGIN;
    }
    for (const b of this.gulls) {
      const flap = Math.sin(t * 3.4 + b.phase);
      const w = 30 * b.size;
      const lift = flap * 9 * b.size;
      const x = ((((b.x0 + b.speed * t + MARGIN) % (WIDE + 400)) + WIDE + 400) % (WIDE + 400)) - MARGIN;
      const y = b.y0 + Math.sin(t * 0.5 + b.phase) * 14;
      b.g.clear();
      b.g.moveTo(x - w, y - lift).quadraticCurveTo(x - w * 0.45, y - 8 * b.size - lift * 0.4, x, y).quadraticCurveTo(x + w * 0.45, y - 8 * b.size - lift * 0.4, x + w, y - lift);
      b.g.stroke({ width: 4.2 * b.size, color: 0x3d4a5c, alpha: 0.8, cap: 'round', join: 'round' });
    }
    if (this.flag) {
      const { mesh, rest, w } = this.flag;
      const pos = mesh.geometry.positions;
      for (let i = 0; i < rest.length; i += 2) {
        const x = rest[i];
        const k = x / w;
        pos[i] = x * (1 - 0.05 * k);
        pos[i + 1] = rest[i + 1] + Math.sin(x * 0.07 - t * 6.2) * 7 * k + k * 6;
      }
      mesh.geometry.getBuffer('aPosition').update();
    }
    const riverDepth = this.layers.find((l) => l.name === 'river')!.depth;
    this.river.update(t, this.app.renderer, camX, riverDepth);
    this.coco.update(t);
    // the bus: in from the left, across, and round again; its wheels turn with the distance
    const period = 26;
    const p = ((t + 1.6) % period + period) % period;
    const bx = -560 + p * 210;
    const by = 1978 + Math.sin(t * 8.5) * 0.7;
    this.bus.node.position.set(bx, by);
    this.bus.shadow.position.set(bx + 18, 1984);
    for (const w of this.bus.wheels) w.rotation = (p * 210) / 34;
    for (const wk of this.walkers) {
      const x = wk.x0 + wk.dir * wk.speed * t;
      const span = WIDE;
      const xx = ((((x + MARGIN) % span) + span) % span) - MARGIN;
      wk.node.position.set(xx, wk.y - Math.abs(Math.sin(t * 5.2)) * 2.2);
      wk.shadow.position.set(xx + 6, wk.y + 2);
    }
  }
}
