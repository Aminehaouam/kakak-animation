import { clamp, ease, lerp, type Ease } from '../../lib/anim';
import type { Pt } from '../../lib/path';
import type { MapCamera } from './UkMap';
import { MAP_H, MAP_W } from './projection';

export interface Padding {
  top: number;
  right: number;
  bottom: number;
  left: number;
}

/** The camera that fits a box of map units into the free part of the view. */
export function frameCamera(points: Pt[], view: { width: number; height: number }, pad: Padding, margin = 40, maxZoom = 6): MapCamera {
  const xs = points.map((p) => p.x);
  const ys = points.map((p) => p.y);
  const [x0, x1, y0, y1] = [Math.min(...xs) - margin, Math.max(...xs) + margin, Math.min(...ys) - margin, Math.max(...ys) + margin];
  const freeW = Math.max(view.width - pad.left - pad.right, 50);
  const freeH = Math.max(view.height - pad.top - pad.bottom, 50);
  const fit = Math.min(freeW / MAP_W, freeH / MAP_H);
  const s = Math.min(freeW / (x1 - x0), freeH / (y1 - y0));
  const zoom = clamp(s / fit, 0.85, maxZoom);
  const sz = fit * zoom;
  return {
    x: (x0 + x1) / 2 + (pad.right - pad.left) / (2 * sz),
    y: (y0 + y1) / 2 + (pad.bottom - pad.top) / (2 * sz),
    zoom,
  };
}

/** Blend two cameras; zoom moves in log space so it feels even. */
export function mixCamera(a: MapCamera, b: MapCamera, u: number, e: Ease = 'inOut'): MapCamera {
  const k = ease[e](clamp(u));
  return { x: lerp(a.x, b.x, k), y: lerp(a.y, b.y, k), zoom: Math.exp(lerp(Math.log(a.zoom), Math.log(b.zoom), k)) };
}

/** Piecewise camera keyframes [[time, camera], ...]. */
export function cameraAt(t: number, frames: Array<[number, MapCamera, Ease?]>): MapCamera {
  if (t <= frames[0][0]) return frames[0][1];
  for (let i = 1; i < frames.length; i++) {
    if (t <= frames[i][0]) {
      const [t0, c0] = frames[i - 1];
      const [t1, c1, e] = frames[i];
      return mixCamera(c0, c1, (t - t0) / (t1 - t0), e ?? 'inOut');
    }
  }
  return frames[frames.length - 1][1];
}
