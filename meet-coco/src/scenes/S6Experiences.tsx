import { useMemo } from 'react';
import { sound } from '../audio/sound';
import { VIGNETTES, VH, VW } from '../art/Vignettes';
import { CocoActor } from '../components/coco/CocoActor';
import { FlightPlan, type Leg } from '../components/coco/flight';
import { cameraAt } from '../components/map/camera';
import { Stage, useViewport } from '../components/stage/Stage';
import { ease, fade, progress } from '../lib/anim';
import { smooth, Track } from '../lib/path';
import { useCues } from '../lib/useStory';
import type { SceneProps } from './types';
import './scenes.css';

const W = 1600;
const H = 1000;
const CARD_W = 440;
const CARD_H = (CARD_W * VH) / VW;
// a board-game route: left to right on top, back right to left below
const CARDS = [
  { x: 290, y: 300 },
  { x: 800, y: 270 },
  { x: 1310, y: 300 },
  { x: 1310, y: 720 },
  { x: 800, y: 750 },
  { x: 290, y: 720 },
].map((c, i) => ({ ...c, tilt: [-1.6, 1.2, -1, 1.4, -1.2, 1][i] }));
const STEP = 1.95;
const FIRST = 0.7;
const focusAt = (i: number) => FIRST + i * STEP;
const T_OVERVIEW = focusAt(6) + 0.2;

const ICONS = [
  // plane, taxi, cup, key, camera between consecutive cards
  'M2 12 l8 -2 6 -8 h2 l-3 8 6 -1 2 -3 h2 l-1 4 1 4 h-2 l-2 -3 -6 -1 3 8 h-2 l-6 -8 -8 -2z',
  'M3 14 v-4 l3 -5 h12 l3 5 v4 h-2 a2 2 0 0 1 -4 0 h-6 a2 2 0 0 1 -4 0z M7 9 h10 l-2 -3 h-6z',
  'M4 7 h13 v5 a6 6 0 0 1 -6 6 h-1 a6 6 0 0 1 -6 -6z M17 8 h2 a3 3 0 0 1 0 6 h-2',
  'M8 4 a5 5 0 1 1 0 10 a5 5 0 1 1 0 -10z M12 11 l9 9 -2 2 -2 -2 -2 2 -2 -2 -3 -3',
  'M3 8 h4 l2 -3 h6 l2 3 h4 v11 h-18z M12 10 a4 4 0 1 1 0 8 a4 4 0 1 1 0 -8z',
];

export function S6Experiences({ t, active, reduced }: SceneProps) {
  const vp = useViewport();
  const wide = !vp.portrait;
  const route = useMemo(() => new Track(smooth(CARDS.map((c) => ({ x: c.x, y: c.y + CARD_H / 2 + 34 })), 18)), []);
  const focus = Math.min(Math.max(Math.floor((t - FIRST + STEP * 0.5) / STEP), 0), 5);

  // Coco hops along the route, perching on the top edge of each card in turn
  const plan = useMemo(() => {
    // on the left of each card's top edge; the speech bubble sits on the right
    const top = (i: number) => ({ x: CARDS[i].x - CARD_W * 0.3, y: CARDS[i].y - CARD_H / 2 - 4 });
    const legs: Leg[] = CARDS.slice(1).map((_, k) => {
      const a = top(k);
      const b = top(k + 1);
      return { start: focusAt(k + 1) - 0.9, duration: 1.0, path: [a, { x: (a.x + b.x) / 2, y: Math.min(a.y, b.y) - 110 }, b], land: 'perch' };
    });
    return new FlightPlan(legs, { at: top(0), mode: 'perch' });
  }, []);
  const fl = reduced ? plan.settled(focusAt(focus)) : plan.at(t);

  const cardCam = (i: number) => ({ x: CARDS[i].x, y: CARDS[i].y - 10, zoom: wide ? 2.05 : 1 });
  const overview = { x: W / 2, y: H / 2, zoom: 1 };
  const frames: Array<[number, { x: number; y: number; zoom: number }]> = [[0, cardCam(0)]];
  CARDS.forEach((_, i) => {
    frames.push([focusAt(i) - 0.35, cardCam(i)]);
    frames.push([focusAt(i) + STEP - 0.95, cardCam(i)]);
  });
  if (wide) frames.push([T_OVERVIEW + 1.2, overview]);
  const camera = reduced ? (wide ? overview : cardCam(focus)) : cameraAt(t, frames);
  const routeDrawn = reduced ? 1 : ease.inOut(progress(t, 0.4, T_OVERVIEW + 0.6));

  useCues(t, [...CARDS.map((_, i) => [focusAt(i) - 0.2, () => sound.play('pop', { volume: 0.5 })] as [number, () => void]), ...CARDS.slice(1).map((_, k) => [focusAt(k + 1) - 1.0, () => sound.play('flap', { volume: 0.5 })] as [number, () => void])], active);

  return (
    <div className="s6">
      <Stage width={W} height={H} camera={camera} className="s6__stage">
        <svg viewBox={`0 0 ${W} ${H}`} aria-hidden>
          <defs>
            <pattern id="dots-paper" width="22" height="22" patternUnits="userSpaceOnUse">
              <circle cx="2" cy="2" r="1.6" fill="#d8ccb2" />
            </pattern>
          </defs>
          <rect width={W} height={H} fill="#f3ead8" />
          <rect width={W} height={H} fill="url(#dots-paper)" />
          <path d={route.d(routeDrawn)} fill="none" stroke="#cf4339" strokeWidth={5} strokeDasharray="2 14" strokeLinecap="round" />
          {CARDS.slice(0, 5).map((c, i) => {
            const n = CARDS[i + 1];
            const mx = (c.x + n.x) / 2 + (i === 2 ? 210 : 0);
            const my = (c.y + n.y) / 2 + CARD_H / 2 + (i === 2 ? -170 : 34);
            const o = reduced ? 1 : fade(t, focusAt(i + 1) - 0.6, 0.4);
            return (
              <g key={i} transform={`translate(${mx - 22} ${my - 22})`} opacity={o}>
                <circle cx={22} cy={22} r={26} fill="#fffaf0" stroke="#cf4339" strokeWidth={3} />
                <g transform="translate(10 10)">
                  <path d={ICONS[i]} fill="#2b3a4a" />
                </g>
              </g>
            );
          })}
        </svg>
        {VIGNETTES.map((v, i) => {
          const c = CARDS[i];
          const on = reduced ? 1 : ease.outBack(progress(t, focusAt(i) - 0.5, 0.6));
          const bubble = reduced ? 1 : fade(t, focusAt(i) + 0.35, 0.4);
          return (
            <figure
              key={v.id}
              className={`xp-card${focus === i ? ' is-focus' : ''}`}
              style={{ left: c.x - CARD_W / 2, top: c.y - CARD_H / 2, width: CARD_W, transform: `rotate(${c.tilt}deg) scale(${0.86 + 0.14 * on})`, opacity: Math.min(on * 1.4, 1) }}
            >
              <div className="xp-card__art" style={{ height: CARD_H }}>
                <v.Component t={t} still={reduced} />
              </div>
              <figcaption className="xp-card__label">
                <b>{i + 1}</b>
                {v.title}
              </figcaption>
              <p className={`xp-card__bubble${wide ? '' : ' xp-card__bubble--inside'}`} style={{ opacity: bubble, transform: `translateY(${(1 - bubble) * 8}px)` }}>
                “{v.phrase}”
              </p>
            </figure>
          );
        })}
        <CocoActor state={fl} height={118} shadow={0.8} still={reduced} cue={t > T_OVERVIEW + 0.8 ? { kind: 'excite', id: 1 } : null} />
      </Stage>
    </div>
  );
}
