// The Thames: painted water, the far bank mirrored live into a render texture and rippled by a
// drifting displacement map, a deepening wash toward us, moving ripple highlights, sun glints,
// and boats with their own reflections and wakes.
import { Container, DisplacementFilter, Matrix, RenderTexture, Sprite, TilingSprite, type Renderer } from 'pixi.js';
import type { Library } from './assets';
import { glint, vertical, wake } from './fx';

const clamp = (v: number, a = 0, b = 1) => Math.min(Math.max(v, a), b);

export interface RiverOptions {
  waterTop: number;
  waterBottom: number;
  width: number;
  margin: number;
  /** the far bank, rendered into the reflection each frame */
  source: Container;
}

interface Boat {
  sprite: Sprite;
  mirror: Sprite;
  wakes: Sprite[];
  y: number;
  speed: number;
  scale: number;
  dir: 1 | -1;
  x0: number;
  span: number;
}

export class River {
  /** water, reflections and ripples (sits at the river's depth) */
  readonly water = new Container();
  /** boats and their wakes (drawn over the water) */
  readonly boats = new Container();
  private rt: RenderTexture;
  private mirror: Sprite;
  private reflections = new Container();
  private disp: Sprite;
  private ripples: TilingSprite[] = [];
  private glints: Array<{ s: Sprite; phase: number; rate: number }> = [];
  private list: Boat[] = [];
  private scale = 0.36;
  private height = 400;

  constructor(private lib: Library, private o: RiverOptions) {
    const { waterTop, waterBottom, width, margin } = o;
    const base = lib.sprite('water');
    base.position.set(0, waterTop);
    this.water.addChild(base);
    // the live mirror of the far bank, flipped below the waterline
    this.rt = RenderTexture.create({ width: Math.ceil(width * this.scale), height: Math.ceil(this.height * this.scale), resolution: 1 });
    this.mirror = new Sprite(this.rt);
    this.mirror.scale.set(1 / this.scale, -1 / this.scale);
    this.mirror.position.set(-margin, waterTop + this.height);
    this.mirror.tint = 0x86b9de;
    this.mirror.alpha = 0.62;
    this.reflections.addChild(this.mirror);
    // ripples in the reflections: a tiling displacement map that drifts slowly
    const dtex = lib.tex.water_displace;
    dtex.source.addressMode = 'repeat';
    this.disp = new Sprite(dtex);
    this.disp.scale.set(3.2, 0.7);
    this.disp.renderable = false;
    this.water.addChild(this.disp);
    this.reflections.filters = [new DisplacementFilter({ sprite: this.disp, scale: { x: 26, y: 7 } })];
    this.water.addChild(this.reflections);
    // deeper, bluer water toward us: the mirror fades as the river comes closer
    const depth = new Sprite(vertical(256, [[0, 'rgba(29,96,160,0)'], [0.25, 'rgba(29,96,160,0.18)'], [1, 'rgba(22,82,142,0.78)']]));
    depth.position.set(-margin, waterTop);
    depth.width = width;
    depth.height = waterBottom - waterTop;
    this.water.addChild(depth);
    // a bright line where the water meets the far wall
    const edge = new Sprite(vertical(32, [[0, 'rgba(255,255,255,0.0)'], [0.4, 'rgba(235,246,252,0.55)'], [1, 'rgba(235,246,252,0)']]));
    edge.position.set(-margin, waterTop - 2);
    edge.width = width;
    edge.height = 14;
    this.water.addChild(edge);
    // moving ripple highlights, two layers drifting against each other
    const rtex = lib.tex.water_ripples;
    rtex.source.addressMode = 'repeat';
    for (const [alpha, sy] of [[0.17, 0.34], [0.1, 0.5]] as const) {
      const r = new TilingSprite({ texture: rtex, width, height: waterBottom - waterTop });
      r.position.set(-margin, waterTop);
      r.tileScale.set(1, sy);
      r.alpha = alpha;
      r.blendMode = 'add';
      this.ripples.push(r);
      this.water.addChild(r);
    }
    // sun glints along the sunlit left reach
    const gt = glint();
    for (let i = 0; i < 46; i++) {
      const s = new Sprite(gt);
      s.anchor.set(0.5);
      const rnd = (k: number) => (Math.sin(i * 12.9898 + k * 78.233) * 43758.5453) % 1;
      const fx = Math.abs(rnd(1));
      const fy = Math.abs(rnd(2));
      s.position.set(150 + fx * 1900, waterTop + 30 + fy ** 1.4 * (waterBottom - waterTop - 60));
      s.scale.set(0.35 + Math.abs(rnd(3)) * 0.55);
      s.blendMode = 'add';
      this.glints.push({ s, phase: Math.abs(rnd(4)) * 10, rate: 0.6 + Math.abs(rnd(5)) * 1.3 });
      this.water.addChild(s);
    }
  }

  addBoat(name: string, opts: { y: number; speed: number; scale: number; dir: 1 | -1; x0: number; span: number }) {
    const sprite = this.lib.sprite(name);
    const mirror = this.lib.sprite(name);
    sprite.scale.set(opts.scale * opts.dir, opts.scale);
    mirror.scale.set(opts.scale * opts.dir, -opts.scale * 0.9);
    mirror.alpha = 0.32;
    mirror.tint = 0x9cc6e6;
    const wakes: Sprite[] = [];
    const wt = wake();
    for (let k = 0; k < 3; k++) {
      const w = new Sprite(wt);
      w.anchor.set(1, 0.5);
      w.alpha = 0.6 - k * 0.15;
      wakes.push(w);
      this.boats.addChild(w);
    }
    this.boats.addChild(sprite);
    this.reflections.addChild(mirror);
    this.list.push({ sprite, mirror, wakes, ...opts });
  }

  /** depth: the parallax depth of the layer holding the water; the mirror cancels it, since the
   * far bank it reflects has already moved with its own depths */
  update(t: number, renderer: Renderer, camX: number, depth: number) {
    const { waterTop } = this.o;
    this.mirror.x = -this.o.margin + camX * depth;
    // refresh the mirror from the far bank as it is drawn right now
    const m = new Matrix().translate(this.o.margin, -(waterTop - this.height)).scale(this.scale, this.scale);
    renderer.render({ container: this.o.source, target: this.rt, clear: true, transform: m });
    this.disp.position.set(-t * 38, t * 6);
    this.ripples[0].tilePosition.set(t * 14, 0);
    this.ripples[1].tilePosition.set(-t * 9 + 300, 120);
    for (const g of this.glints) {
      const v = Math.sin(t * g.rate + g.phase);
      g.s.alpha = clamp(v) ** 6 * 0.9;
    }
    // boats travel their reach and loop; the water layer moves with `depth` for parallax
    for (const b of this.list) {
      const p = ((t * b.speed + b.x0) % b.span + b.span) % b.span;
      const x = b.dir > 0 ? -400 + p : 4240 - p;
      const bob = Math.sin(t * 1.7 + b.y) * 1.6;
      b.sprite.position.set(x, b.y + bob);
      b.mirror.position.set(x, b.y + 4);
      b.wakes.forEach((w, k) => {
        w.scale.set(b.dir * (0.9 + k * 0.5) * b.scale * 1.4, (0.45 + k * 0.4) * b.scale);
        w.position.set(x - b.dir * (b.sprite.width * 0.5 - 18) - b.dir * k * 30, b.y - 4 + k * 3);
        w.alpha = (0.5 - k * 0.13) * (0.8 + 0.2 * Math.sin(t * 3 + k));
      });
    }
  }
}
