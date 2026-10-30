import { useMemo, type ReactNode } from 'react';
import { sound } from '../audio/sound';
import { Airport, AIRPORT, Cafe, CAFE, Market, MARKET, TAXI, TaxiRain, VH, VW } from '../art/Vignettes';
import { CocoActor } from '../components/coco/CocoActor';
import { FlightPlan } from '../components/coco/flight';
import { Stage, useViewport } from '../components/stage/Stage';
import { ease, keys, progress } from '../lib/anim';
import { useCues } from '../lib/useStory';
import type { SceneProps } from './types';
import './scenes.css';

const still = (x: number, y: number, facing: 'left' | 'right' = 'right', mode: 'stand' | 'perch' = 'perch') => ({ x, y, mode, facing, tilt: 0, scale: 1 });
const APPEAR = [0.3, 1.1, 1.9, 2.7];

/** Coco living it: at passport control, in a taxi, over tea, and off to find a street. */
export function S7LiveIt({ t, active, reduced }: SceneProps) {
  const vp = useViewport();
  const wide = !vp.portrait;
  // landscape: a 2 x 2 grid under the caption; portrait: one column the camera travels down
  const W = wide ? 1600 : 640;
  const H = wide ? 1000 : 1760;
  const k = wide ? 0.88 : 1; // panel scale
  const slots = wide
    ? [
        { x: 800 - VW * k - 14, y: 205 },
        { x: 814, y: 205 },
        { x: 800 - VW * k - 14, y: 205 + VH * k + 18 },
        { x: 814, y: 205 + VH * k + 18 },
      ]
    : [0, 1, 2, 3].map((i) => ({ x: 20, y: 150 + i * 400 }));
  const camY = reduced ? H / 2 : wide ? H / 2 : keys(t, [[0, 520], [3.4, 1000], [6.6, 1350], [9, 1350]]);

  const stamp = reduced ? 0 : Math.max(0, Math.sin(Math.min(Math.max((t - 2.4) / 0.35, 0), 1) * Math.PI), Math.sin(Math.min(Math.max((t - 3.4) / 0.35, 0), 1) * Math.PI));
  const city = useMemo(
    () =>
      new FlightPlan(
        [{ start: 4.4, duration: 1.8, path: [{ x: -60, y: 260 }, { x: 200, y: 110 }, { x: 380, y: 30 }, MARKET.signTop], land: 'perch', ease: 'out' }],
        { at: { x: -60, y: 260 }, mode: 'fly' },
      ),
    [],
  );
  const flCity = reduced ? still(MARKET.signTop.x, MARKET.signTop.y, 'left') : city.at(t);
  const party = t > 7.6 ? { kind: 'excite' as const, id: 2 } : null;

  useCues(t, [[2.4, () => sound.play('stamp', { volume: 0.8 })], [3.4, () => sound.play('stamp', { volume: 0.8 })], [4.2, () => sound.play('flap')], [5.0, () => sound.play('chirp')], [7.4, () => sound.play('ding')]], active);

  const panel = (i: number, children: ReactNode, art: ReactNode, label: string) => {
    const on = reduced ? 1 : ease.outBack(progress(t, APPEAR[i], 0.6));
    const s = slots[i];
    return (
      <figure className="live-panel" style={{ left: s.x, top: s.y, width: VW, height: VH, opacity: Math.min(on * 1.5, 1), transform: `scale(${k * (0.9 + 0.1 * on)})` }} aria-label={label}>
        <div className="live-panel__art">{art}</div>
        <div className="live-panel__actors">{children}</div>
      </figure>
    );
  };

  return (
    <div className="s7">
      <Stage width={W} height={H} camera={{ x: W / 2, y: camY, zoom: 1 }}>
        <div className="s7__bg" />
        {panel(
          0,
          <CocoActor state={still(AIRPORT.perch.x, AIRPORT.perch.y, 'right')} height={110} still={reduced} cue={t > 1.6 ? { kind: 'look', id: 1 } : party} />,
          <Airport t={t} still={reduced} stamp={stamp} />,
          'Coco watches the passport check',
        )}
        {panel(
          1,
          <div className="live-window" style={{ left: TAXI.window.x, top: TAXI.window.y, width: TAXI.window.w, height: TAXI.window.h }}>
            <CocoActor state={still(TAXI.window.w * 0.46, TAXI.window.h + 62, 'right', 'stand')} height={118} still={reduced} cue={t > 2.6 ? { kind: 'look', id: 1 } : party} />
            <i className="live-window__glass" />
          </div>,
          <TaxiRain t={t} still={reduced} />,
          'Coco looks out of the taxi window',
        )}
        {panel(
          2,
          <CocoActor state={still(CAFE.perch.x, CAFE.perch.y, 'left', 'stand')} height={124} still={reduced} cue={t > 3.6 ? { kind: 'excite', id: 1 } : null} />,
          <Cafe t={t} still={reduced} />,
          'Coco beside a cup of tea',
        )}
        {panel(3, <CocoActor state={flCity} height={104} still={reduced} cue={party} />, <Market t={t} still={reduced} />, 'Coco flies to a street sign')}
        <div className="s7__dim" style={{ opacity: reduced ? (t >= 7.4 ? 0.5 : 0) : 0.55 * ease.out(progress(t, 7.2, 0.8)) }} />
      </Stage>
    </div>
  );
}
