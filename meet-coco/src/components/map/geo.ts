// Geometry prepared once from ukmap.json and places.ts: the route, stop positions, forest trees,
// sea wave marks and label anchors, all in map units (km).
import data from './ukmap.json';
import { CORRIDORS, FORESTS, STOPS } from '../../config/places';
import { rng } from '../../lib/anim';
import { smooth, Track, type Pt } from '../../lib/path';
import { MAP_H, MAP_W, toMap } from './projection';

export const MAP = data;
export const EXTENT = { x0: data.extent[0], y0: data.extent[1], x1: data.extent[2], y1: data.extent[3] };

/** Polygon rings of the British Isles' land, for point-in-land tests. */
const LAND_RINGS: Pt[][] = data.land
  .split('M')
  .filter(Boolean)
  .map((part) =>
    part
      .replace(/Z/g, '')
      .split(/L|\s/)
      .filter(Boolean)
      .map((pair) => {
        const [x, y] = pair.split(',').map(Number);
        return { x, y };
      }),
  );

export function onLand(p: Pt): boolean {
  let inside = false;
  for (const ring of LAND_RINGS) {
    for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
      const a = ring[i];
      const b = ring[j];
      if (a.y > p.y !== b.y > p.y && p.x < ((b.x - a.x) * (p.y - a.y)) / (b.y - a.y) + a.x) inside = !inside;
    }
  }
  return inside;
}

// ---- the route

export const STOP_POINTS: Record<string, Pt> = Object.fromEntries(STOPS.map((s) => [s.id, toMap(s.lonlat)]));

const routeWaypoints: Pt[] = [];
STOPS.forEach((stop, i) => {
  routeWaypoints.push(STOP_POINTS[stop.id]);
  const next = STOPS[i + 1];
  if (next) routeWaypoints.push(...(CORRIDORS[`${stop.id}-${next.id}`] ?? []).map(toMap));
});
export const ROUTE = new Track(smooth(routeWaypoints, 10));
/** Fraction of the route at each stop. */
export const STOP_AT: Record<string, number> = Object.fromEntries(STOPS.map((s) => [s.id, ROUTE.fractionNear(STOP_POINTS[s.id])]));

// ---- decoration

export interface Tree {
  x: number;
  y: number;
  s: number;
  tone: number;
  conifer: boolean;
}

/** Tree clusters at real forests, scattered with a fixed seed and kept on land. */
export const TREES: Tree[] = (() => {
  const r = rng(20251030);
  const trees: Tree[] = [];
  for (const [, lon, lat, radius] of FORESTS) {
    const c = toMap([lon, lat]);
    const n = Math.round(4 + radius * 0.9);
    const conifers = lat > 54.4 || lon < -5;
    for (let i = 0, tries = 0; i < n && tries < n * 6; tries++) {
      const a = r() * Math.PI * 2;
      const d = Math.sqrt(r()) * radius;
      const p = { x: c.x + Math.cos(a) * d, y: c.y + Math.sin(a) * d * 0.8 };
      if (!onLand(p)) continue;
      trees.push({ ...p, s: 0.8 + r() * 0.45, tone: r(), conifer: conifers ? r() < 0.8 : r() < 0.25 });
      i++;
    }
  }
  return trees.sort((a, b) => a.y - b.y);
})();

/** Little wave marks scattered over open water. */
export const WAVES: Pt[] = (() => {
  const r = rng(77);
  const out: Pt[] = [];
  const near = (p: Pt) => onLand(p) || onLand({ x: p.x + 14, y: p.y }) || onLand({ x: p.x - 14, y: p.y }) || onLand({ x: p.x, y: p.y + 12 }) || onLand({ x: p.x, y: p.y - 12 });
  for (let tries = 0; out.length < 46 && tries < 2000; tries++) {
    const p = { x: -160 + r() * (MAP_W + 320), y: -60 + r() * (MAP_H + 120) };
    if (near(p) || out.some((q) => Math.hypot(q.x - p.x, q.y - p.y) < 70)) continue;
    out.push(p);
  }
  return out;
})();
