// Coco: the body and wings cut from the original character image, rigged here. He flies in
// over the river, flares, lands on the balustrade and settles; everything is a function of time.
import { Container, Graphics, Sprite } from 'pixi.js';
import type { Library } from './assets';
import { contactShadow } from './fx';

const DEG = Math.PI / 180;
const clamp = (v: number, a = 0, b = 1) => Math.min(Math.max(v, a), b);
const smooth = (x: number) => x * x * (3 - 2 * x);
const easeOut = (x: number) => 1 - (1 - x) ** 3;
type Pt = [number, number];

function bezier(p: Pt[], u: number): Pt {
  const [a, b, c, d] = p;
  const v = 1 - u;
  return [v ** 3 * a[0] + 3 * v * v * u * b[0] + 3 * v * u * u * c[0] + u ** 3 * d[0], v ** 3 * a[1] + 3 * v * v * u * b[1] + 3 * v * u * u * c[1] + u ** 3 * d[1]];
}

export interface CocoTiming {
  /** when he appears at the top left, and when his feet touch the stone */
  start: number;
  land: number;
}

export class Coco {
  readonly root = new Container();
  readonly shadow: Sprite;
  private tilt = new Container();
  private body: Sprite;
  private wing: Sprite;
  private far: Sprite;
  private lid = new Graphics();
  private path: Pt[];

  constructor(lib: Library, private perch: Pt, private timing: CocoTiming, private size = 0.45) {
    const meta = lib.man.coco_body as unknown as { shoulder: Pt; eye: Pt; eyeR: number };
    this.body = lib.sprite('coco_body');
    this.wing = lib.sprite('coco_wing');
    this.far = lib.sprite('coco_wing_far');
    const [sx, sy] = meta.shoulder;
    this.wing.position.set(sx, sy);
    this.far.position.set(sx - 18, sy - 10);
    this.far.scale.set(0.94);
    // the eyelid: plumage-grey, it drops over the eye for a blink
    this.lid.ellipse(0, meta.eyeR * 0.95, meta.eyeR * 0.98, meta.eyeR * 0.98).fill({ color: 0xd8d8de });
    this.lid.position.set(meta.eye[0], meta.eye[1] - meta.eyeR * 0.95);
    this.lid.scale.y = 0;
    this.tilt.addChild(this.far, this.body, this.wing, this.lid);
    // tilt about the middle of the body, so flight and landing pivot naturally
    this.tilt.pivot.set(0, -230);
    this.tilt.position.set(0, -230);
    this.root.addChild(this.tilt);
    this.root.scale.set(size);
    this.shadow = new Sprite(contactShadow());
    this.shadow.anchor.set(0.5);
    // the flight path: in from the upper left, sweeping down over the river onto the stone
    const [px, py] = perch;
    this.path = [[-320, 420], [420, 210], [px - 520, py - 520], [px, py]];
  }

  update(t: number) {
    const { start, land } = this.timing;
    const [px, py] = this.perch;
    let x: number, y: number, tiltDeg: number, wingDeg: number, squash = 1;
    if (t < land) {
      // flying: progress along the path, slowing toward the perch
      const u = clamp((t - start) / (land - start));
      const k = 1 - (1 - u) ** 1.8;
      [x, y] = bezier(this.path, k);
      const [x2, y2] = bezier(this.path, Math.min(k + 0.01, 1));
      const pitch = Math.atan2(y2 - y, Math.max(x2 - x, 1e-3)) / DEG;
      const flare = smooth(clamp((u - 0.78) / 0.22));
      tiltDeg = (1 - flare) * clamp(pitch * 0.55 + 12, -6, 34) + flare * -14;
      // wingbeats: brisk beats with short glides, then quick braking beats as he flares
      const beat = 3.1 + flare * 1.6;
      const phase = (t - start) * beat * Math.PI * 2;
      const glide = 0.5 + 0.5 * Math.sin((t - start) * 1.3);
      const stroke = Math.sin(phase + 0.35 * Math.sin(phase)); // a faster downstroke
      const amp = 78 * (1 - glide * 0.55 * (1 - flare));
      wingDeg = 64 + stroke * amp + flare * 22;
      this.root.visible = t >= start;
    } else {
      // perched: touch down with a little squash, fold the wings, then breathe and blink
      const dt = t - land;
      x = px;
      y = py;
      squash = 1 - 0.07 * Math.sin(clamp(dt / 0.35) * Math.PI) * (1 - clamp(dt / 0.35));
      tiltDeg = -14 * (1 - easeOut(clamp(dt / 0.45))) + 1.2 * Math.sin(dt * 0.9) * clamp(dt - 1);
      const fold = easeOut(clamp(dt / 0.5));
      wingDeg = (86 + 30 * Math.sin(clamp(dt / 0.5) * Math.PI)) * (1 - fold) + 2.2 * Math.sin(dt * 1.7) * clamp(dt - 1);
      this.root.visible = true;
    }
    this.root.position.set(x, y);
    this.tilt.rotation = tiltDeg * DEG;
    const breathe = t >= land ? 1 + 0.012 * Math.sin((t - land) * 2.4) : 1;
    this.tilt.scale.set(1 / squash ** 0.5, squash * breathe);
    this.wing.rotation = wingDeg * DEG;
    this.far.rotation = (wingDeg * 0.92 - 6) * DEG;
    // the far wing hides behind the body once folded
    this.far.alpha = clamp((wingDeg - 8) / 20);
    // blink every few seconds once he has landed
    const since = t - land - 0.8;
    const cyc = ((since % 3.7) + 3.7) % 3.7;
    const blink = since > 0 && cyc < 0.16 ? Math.sin((cyc / 0.16) * Math.PI) : 0;
    this.lid.scale.y = blink;
    // his shadow on the stone appears as he comes down to it
    const above = py - y;
    this.shadow.position.set(x + 8 + above * 0.08, py + 3);
    this.shadow.alpha = 0.85 * clamp(1 - above / 380) * (this.root.visible ? 1 : 0);
    const spread = 1 + above / 600;
    this.shadow.scale.set((190 * this.size * 2.2 * spread) / 256, (30 * spread) / 256);
  }
}
