import data from './ukmap.json';
import type { LonLat } from '../../config/places';
import type { Pt } from '../../lib/path';

// The same spherical transverse Mercator as tools/map/build_map.py, so markers land exactly on
// the generated coastline. Map units are kilometres from the map's top-left corner.
const { sphere: R, lon0, lat0, x0, yTop } = data.projection;
const rad = Math.PI / 180;

export function toMap([lon, lat]: LonLat): Pt {
  const lam = (lon - lon0) * rad;
  const phi = lat * rad;
  const b = Math.cos(phi) * Math.sin(lam);
  const x = 0.5 * R * Math.log((1 + b) / (1 - b));
  const y = R * (Math.atan2(Math.tan(phi), Math.cos(lam)) - lat0 * rad);
  return { x: x - x0, y: yTop - y };
}

export function fromMap({ x, y }: Pt): LonLat {
  const d = (yTop - y) / R + lat0 * rad;
  const xr = (x + x0) / R;
  const lat = Math.asin(Math.sin(d) / Math.cosh(xr)) / rad;
  const lon = lon0 + Math.atan2(Math.sinh(xr), Math.cos(d)) / rad;
  return [lon, lat];
}

export const MAP_W = data.size[0];
export const MAP_H = data.size[1];
