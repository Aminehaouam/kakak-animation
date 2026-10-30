// Small, dependency-free animation helpers. Every scene is a pure function of its clock time,
// so the story can pause, seek and be screenshot at any moment.

export const clamp = (v: number, lo = 0, hi = 1) => Math.min(hi, Math.max(lo, v));
export const lerp = (a: number, b: number, t: number) => a + (b - a) * t;

/** 0..1 progress of t through [start, start + duration]. */
export const progress = (t: number, start: number, duration: number) =>
  duration <= 0 ? (t >= start ? 1 : 0) : clamp((t - start) / duration);

export const ease = {
  linear: (x: number) => x,
  inOut: (x: number) => (x < 0.5 ? 4 * x * x * x : 1 - (-2 * x + 2) ** 3 / 2),
  out: (x: number) => 1 - (1 - x) ** 3,
  in: (x: number) => x * x * x,
  outBack: (x: number) => {
    const c1 = 1.5;
    const c3 = c1 + 1;
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2;
  },
  sine: (x: number) => -(Math.cos(Math.PI * x) - 1) / 2,
};
export type Ease = keyof typeof ease;

/** Eased value between a and b while t runs from start to start + duration. */
export function tween(t: number, start: number, duration: number, a: number, b: number, e: Ease = 'inOut') {
  return lerp(a, b, ease[e](progress(t, start, duration)));
}

/** Piecewise keyframes [[time, value, ease?], ...] sampled at t (held before / after). */
export function keys(t: number, frames: Array<[number, number, Ease?]>) {
  if (t <= frames[0][0]) return frames[0][1];
  for (let i = 1; i < frames.length; i++) {
    const [t1, v1, e] = frames[i];
    const [t0, v0] = frames[i - 1];
    if (t <= t1) return lerp(v0, v1, ease[e ?? 'inOut'](progress(t, t0, t1 - t0)));
  }
  return frames[frames.length - 1][1];
}

/** Fade in at `start` over `fadeIn`, out at `end` over `fadeOut` (end optional). */
export function fade(t: number, start: number, fadeIn = 0.6, end = Infinity, fadeOut = 0.6) {
  return Math.min(ease.out(progress(t, start, fadeIn)), 1 - ease.inOut(progress(t, end, fadeOut)));
}

/** A deterministic pseudo-random generator, so illustrations look the same on every load. */
export function rng(seed: number) {
  let s = seed >>> 0 || 1;
  return () => {
    s ^= s << 13;
    s ^= s >>> 17;
    s ^= s << 5;
    return (s >>> 0) / 4294967296;
  };
}
