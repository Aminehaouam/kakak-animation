import { useCallback, useEffect, useRef, useState } from 'react';

/** Seconds since the scene started; advances on animation frames while playing. */
export function useSceneClock(sceneKey: number, playing: boolean, initial = 0) {
  const [t, setT] = useState(initial);
  const tRef = useRef(initial);
  const first = useRef(true);

  useEffect(() => {
    if (first.current) {
      first.current = false;
      return;
    }
    tRef.current = 0;
    setT(0);
  }, [sceneKey]);

  useEffect(() => {
    if (!playing) return;
    let raf = 0;
    let last = performance.now();
    const tick = (now: number) => {
      const dt = Math.min((now - last) / 1000, 0.1); // a hidden tab doesn't jump ahead
      last = now;
      tRef.current += dt;
      setT(tRef.current);
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [playing, sceneKey]);

  const seek = useCallback((v: number) => {
    tRef.current = v;
    setT(v);
  }, []);
  return [t, seek] as const;
}

/** Runs each callback once when the clock passes its time while playing forward. */
export function useCues(t: number, cues: Array<[number, () => void]>, enabled = true) {
  const prev = useRef(t);
  useEffect(() => {
    const p = prev.current;
    prev.current = t;
    if (!enabled || t < p || t - p > 0.5) return;
    for (const [at, fn] of cues) if (p < at && t >= at) fn();
  });
}

export function usePrefersReducedMotion() {
  const query = '(prefers-reduced-motion: reduce)';
  const [reduced, setReduced] = useState(() => typeof window !== 'undefined' && window.matchMedia(query).matches);
  useEffect(() => {
    const mq = window.matchMedia(query);
    const on = () => setReduced(mq.matches);
    mq.addEventListener('change', on);
    return () => mq.removeEventListener('change', on);
  }, []);
  return reduced;
}
