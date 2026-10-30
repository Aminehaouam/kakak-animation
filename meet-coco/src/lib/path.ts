// Paths as point lists: smooth Catmull-Rom curves through waypoints, with sampling by arc length
// (position and heading), so Coco and the camera can travel along them at a steady pace.

export type Pt = { x: number; y: number };

/** A dense polyline through the points along a centripetal Catmull-Rom spline. */
export function smooth(points: Pt[], perSegment = 16): Pt[] {
  if (points.length < 3) return points.slice();
  const out: Pt[] = [];
  const p = [points[0], ...points, points[points.length - 1]];
  for (let i = 1; i < p.length - 2; i++) {
    const [p0, p1, p2, p3] = [p[i - 1], p[i], p[i + 1], p[i + 2]];
    const t0 = 0;
    const t1 = t0 + Math.pow(dist(p0, p1) || 1e-6, 0.5);
    const t2 = t1 + Math.pow(dist(p1, p2) || 1e-6, 0.5);
    const t3 = t2 + Math.pow(dist(p2, p3) || 1e-6, 0.5);
    for (let j = 0; j < perSegment; j++) {
      const t = t1 + ((t2 - t1) * j) / perSegment;
      const a1 = mix(p0, p1, (t1 - t) / (t1 - t0), (t - t0) / (t1 - t0));
      const a2 = mix(p1, p2, (t2 - t) / (t2 - t1), (t - t1) / (t2 - t1));
      const a3 = mix(p2, p3, (t3 - t) / (t3 - t2), (t - t2) / (t3 - t2));
      const b1 = mix(a1, a2, (t2 - t) / (t2 - t0), (t - t0) / (t2 - t0));
      const b2 = mix(a2, a3, (t3 - t) / (t3 - t1), (t - t1) / (t3 - t1));
      out.push(mix(b1, b2, (t2 - t) / (t2 - t1), (t - t1) / (t2 - t1)));
    }
  }
  out.push(points[points.length - 1]);
  return out;
}

const dist = (a: Pt, b: Pt) => Math.hypot(b.x - a.x, b.y - a.y);
const mix = (a: Pt, b: Pt, wa: number, wb: number): Pt => ({ x: a.x * wa + b.x * wb, y: a.y * wa + b.y * wb });

export class Track {
  readonly pts: Pt[];
  readonly cum: number[];
  readonly length: number;

  constructor(pts: Pt[]) {
    this.pts = pts;
    this.cum = [0];
    for (let i = 1; i < pts.length; i++) this.cum.push(this.cum[i - 1] + dist(pts[i - 1], pts[i]));
    this.length = this.cum[this.cum.length - 1];
  }

  /** Point and heading (radians) at fraction u of the length. */
  at(u: number): Pt & { angle: number } {
    const s = Math.min(Math.max(u, 0), 1) * this.length;
    let lo = 0;
    let hi = this.cum.length - 1;
    while (hi - lo > 1) {
      const mid = (lo + hi) >> 1;
      if (this.cum[mid] < s) lo = mid;
      else hi = mid;
    }
    const seg = this.cum[hi] - this.cum[lo] || 1;
    const f = (s - this.cum[lo]) / seg;
    const a = this.pts[lo];
    const b = this.pts[hi] ?? a;
    return { x: a.x + (b.x - a.x) * f, y: a.y + (b.y - a.y) * f, angle: Math.atan2(b.y - a.y, b.x - a.x) };
  }

  /** Fraction of the length at the vertex closest to p (for stops on a route). */
  fractionNear(p: Pt): number {
    let best = 0;
    let bestD = Infinity;
    this.pts.forEach((q, i) => {
      const d = dist(p, q);
      if (d < bestD) {
        bestD = d;
        best = i;
      }
    });
    return this.length ? this.cum[best] / this.length : 0;
  }

  /** SVG path data, optionally only up to fraction u. */
  d(u = 1, digits = 1): string {
    const s = u * this.length;
    const parts: string[] = [];
    for (let i = 0; i < this.pts.length; i++) {
      if (this.cum[i] > s) {
        const end = this.at(u);
        parts.push(`${end.x.toFixed(digits)},${end.y.toFixed(digits)}`);
        break;
      }
      parts.push(`${this.pts[i].x.toFixed(digits)},${this.pts[i].y.toFixed(digits)}`);
    }
    return parts.length ? 'M' + parts.join('L') : '';
  }
}
