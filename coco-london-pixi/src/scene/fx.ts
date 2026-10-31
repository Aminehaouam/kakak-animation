// Textures made in code at start-up: soft light, fog, shadows, wakes and glints. They are the
// rendering side of the scene (light and atmosphere), kept separate from the painted artwork.
import { Texture } from 'pixi.js';

function canvas(w: number, h: number): [HTMLCanvasElement, CanvasRenderingContext2D] {
  const c = document.createElement('canvas');
  c.width = w;
  c.height = h;
  return [c, c.getContext('2d')!];
}

type Stops = Array<[number, string]>;

/** A radial gradient on a square canvas (stretch the sprite for ellipses). */
export function radial(size: number, stops: Stops): Texture {
  const [c, g] = canvas(size, size);
  const grad = g.createRadialGradient(size / 2, size / 2, 0, size / 2, size / 2, size / 2);
  for (const [o, col] of stops) grad.addColorStop(o, col);
  g.fillStyle = grad;
  g.fillRect(0, 0, size, size);
  return Texture.from(c);
}

/** A vertical gradient strip (stretch it to any width). */
export function vertical(h: number, stops: Stops): Texture {
  const [c, g] = canvas(4, h);
  const grad = g.createLinearGradient(0, 0, 0, h);
  for (const [o, col] of stops) grad.addColorStop(o, col);
  g.fillStyle = grad;
  g.fillRect(0, 0, 4, h);
  return Texture.from(c);
}

/** A soft contact shadow: dense in the middle, fading to nothing. */
export function contactShadow(): Texture {
  return radial(256, [
    [0, 'rgba(20,24,36,0.62)'],
    [0.35, 'rgba(20,24,36,0.42)'],
    [0.7, 'rgba(20,24,36,0.12)'],
    [1, 'rgba(20,24,36,0)'],
  ]);
}

/** Foam trailing behind a boat: a narrow wedge that fades toward the tail. */
export function wake(): Texture {
  const [c, g] = canvas(512, 64);
  const grad = g.createLinearGradient(0, 0, 512, 0);
  grad.addColorStop(0, 'rgba(255,255,255,0)');
  grad.addColorStop(0.75, 'rgba(255,255,255,0.55)');
  grad.addColorStop(1, 'rgba(255,255,255,0.9)');
  g.fillStyle = grad;
  g.beginPath();
  g.moveTo(0, 30);
  g.quadraticCurveTo(300, 26, 512, 6);
  g.lineTo(512, 58);
  g.quadraticCurveTo(300, 38, 0, 34);
  g.closePath();
  g.fill();
  return Texture.from(c);
}

/** A small four-point sparkle for sun glints on the water. */
export function glint(): Texture {
  const s = 64;
  const [c, g] = canvas(s, s);
  const grad = g.createRadialGradient(s / 2, s / 2, 0, s / 2, s / 2, s / 2);
  grad.addColorStop(0, 'rgba(255,255,250,1)');
  grad.addColorStop(0.18, 'rgba(255,250,235,0.7)');
  grad.addColorStop(1, 'rgba(255,250,235,0)');
  g.fillStyle = grad;
  g.beginPath();
  g.ellipse(s / 2, s / 2, s / 2, s / 9, 0, 0, Math.PI * 2);
  g.fill();
  g.beginPath();
  g.ellipse(s / 2, s / 2, s / 14, s / 3, 0, 0, Math.PI * 2);
  g.fill();
  return Texture.from(c);
}
