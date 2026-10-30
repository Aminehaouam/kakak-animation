import { useMemo, useState } from 'react';
import { sound } from '../audio/sound';
import type { CocoCue } from '../components/coco/Coco';
import { FlightPlan, type Leg } from '../components/coco/flight';
import { cameraAt, frameCamera, type Padding } from '../components/map/camera';
import { ROUTE, STOP_AT, STOP_POINTS } from '../components/map/geo';
import { toMap } from '../components/map/projection';
import { REVEAL, UkMap } from '../components/map/UkMap';
import { useViewport } from '../components/stage/Stage';
import { STOPS } from '../config/places';
import { clamp, ease, fade, progress } from '../lib/anim';
import type { Pt } from '../lib/path';
import { useCues } from '../lib/useStory';
import { RouteCard } from './parts/RouteCard';
import type { SceneProps } from './types';
import './scenes.css';

/** Points along the route between two fractions (for Coco's flights). */
function routeBetween(a: number, b: number, n = 36): Pt[] {
  return Array.from({ length: n + 1 }, (_, i) => ROUTE.at(a + ((b - a) * i) / n));
}

// Coco's flights: in over the Channel to London, then along the drawn route with stops
const T_IN = REVEAL.done + 0.3;
const LEGS: Array<Leg & { from: string | null; to: string }> = [
  { from: null, to: 'london', start: T_IN, duration: 1.6, path: [toMap([0.9, 49.9]), toMap([0.4, 50.7]), STOP_POINTS.london], land: 'stand', ease: 'out' },
  { from: 'london', to: 'birmingham', start: T_IN + 2.3, duration: 2.1, path: routeBetween(STOP_AT.london, STOP_AT.birmingham), land: 'stand', ease: 'inOut' },
  { from: 'birmingham', to: 'liverpool', start: T_IN + 5.0, duration: 1.9, path: routeBetween(STOP_AT.birmingham, STOP_AT.liverpool), land: 'stand', ease: 'inOut' },
  { from: 'liverpool', to: 'edinburgh', start: T_IN + 7.5, duration: 2.6, path: routeBetween(STOP_AT.liverpool, STOP_AT.edinburgh), land: 'stand', ease: 'inOut' },
];
const T_ROUTE_DONE = LEGS[3].start + LEGS[3].duration;

/** How much of the route is drawn: the pen leads Coco a little on each flight. */
function routeProgress(t: number) {
  let u = 0;
  for (const leg of LEGS.slice(1)) {
    const a = STOP_AT[leg.from!];
    const b = STOP_AT[leg.to];
    const k = ease.inOut(clamp(progress(t, leg.start - 0.35, leg.duration) * 1.12));
    if (t >= leg.start - 0.35) u = a + (b - a) * k;
  }
  return u;
}

export function S4Map({ t, active, reduced, onHold }: SceneProps) {
  const vp = useViewport();
  const wide = vp.width >= 900;
  const pad: Padding = wide
    ? { top: 96, right: 76, bottom: 96, left: Math.min(380, vp.width * 0.3) }
    : { top: 70, right: 58, bottom: 100, left: 14 };
  const [held, setHeld] = useState(false);

  const plan = useMemo(() => new FlightPlan(LEGS, { at: toMap([0.9, 49.9]) }), []);
  const cams = useMemo(() => {
    const view = { width: vp.width, height: vp.height };
    const all = frameCamera([toMap([-10.6, 49.9]), toMap([1.8, 60.9])], view, pad, 0, 1);
    const routeAll = frameCamera(Object.values(STOP_POINTS), view, pad, 70, 3);
    const south = frameCamera([STOP_POINTS.london, STOP_POINTS.birmingham, STOP_POINTS.oxford], view, pad, 120, 3);
    const middle = frameCamera([STOP_POINTS.birmingham, STOP_POINTS.liverpool, STOP_POINTS.manchester], view, pad, 140, 3);
    const north = frameCamera([STOP_POINTS.liverpool, STOP_POINTS.edinburgh], view, pad, 110, 3);
    return { all, routeAll, south, middle, north, intro: { ...all, zoom: all.zoom * 1.12 } };
  }, [vp.width, vp.height, pad.left, pad.top, pad.right, pad.bottom]); // eslint-disable-line react-hooks/exhaustive-deps

  const camera = reduced
    ? t < T_IN
      ? cams.all
      : cams.routeAll
    : cameraAt(t, [
        [0, cams.intro],
        [REVEAL.done, cams.all, 'inOut'],
        [T_IN + 1.6, cams.south],
        [LEGS[1].start + 1.6, cams.middle],
        [LEGS[2].start + 1.6, cams.middle],
        [LEGS[3].start + 2.2, cams.north],
        [T_ROUTE_DONE + 1.8, cams.routeAll],
      ]);

  const fl = reduced ? plan.settled(t) : plan.at(t);
  const cocoVisible = t >= T_IN - 0.3;
  // stops: the one Coco is heading for pulses
  const current = LEGS.reduce<string | null>((cur, leg) => (t >= leg.start - 0.3 ? leg.to : cur), null);
  const cue: CocoCue = t >= T_ROUTE_DONE + 0.4 ? { kind: 'excite', id: 1 } : null;

  useCues(
    t,
    [
      [REVEAL.coast, () => sound.play('pen', { duration: 2.4, volume: 0.8 })],
      [REVEAL.terrain, () => sound.play('whoosh', { volume: 0.4 })],
      ...STOPS.map((_, i) => [REVEAL.markers + i * 0.18, () => sound.play('pop', { volume: 0.5 })] as [number, () => void]),
      ...LEGS.flatMap((leg) => [
        [leg.start - 0.25, () => sound.play('flap', { volume: 0.7 })] as [number, () => void],
        [leg.start + leg.duration - 0.1, () => sound.play('chirp', { volume: 0.6 })] as [number, () => void],
      ]),
      ...LEGS.slice(1).map((leg) => [leg.start - 0.3, () => sound.play('pen', { duration: leg.duration, volume: 0.6 })] as [number, () => void]),
    ],
    active,
  );

  const hint = fade(t, T_ROUTE_DONE + 1.2, 0.8);
  return (
    <div className="s4">
      <UkMap
        reveal={reduced ? (t < 0.2 ? 0 : 99) : t}
        route={reduced ? (t >= T_IN ? 1 : 0) : routeProgress(t)}
        current={current}
        camera={camera}
        interactive={active}
        coco={cocoVisible ? { at: fl, mode: fl.mode, facing: fl.facing, tilt: fl.tilt, cue } : null}
        reduced={reduced}
        padding={pad}
        onInteract={() => {
          if (!held) {
            setHeld(true);
            onHold?.(true);
          }
        }}
      />
      {wide && (
        <RouteCard
          t={t}
          appear={fade(t, REVEAL.markers, 0.8)}
          reached={STOPS.filter((s) => routeProgress(t) >= STOP_AT[s.id] - 0.002 || (s.id === 'london' && t >= LEGS[0].start + LEGS[0].duration)).map((s) => s.id)}
          current={current}
        />
      )}
      <p className="map-hint" style={{ opacity: hint }} aria-hidden={hint < 0.5}>
        {wide ? 'Drag, zoom and pick a stop to explore the route' : 'Tap a stop to explore'}
      </p>
    </div>
  );
}
