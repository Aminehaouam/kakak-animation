import { useMemo } from 'react';
import { sound } from '../audio/sound';
import { FlightPlan } from '../components/coco/flight';
import { cameraAt, frameCamera, type Padding } from '../components/map/camera';
import { ROUTE, STOP_AT, STOP_POINTS } from '../components/map/geo';
import { UkMap } from '../components/map/UkMap';
import { useViewport } from '../components/stage/Stage';
import { clamp, ease, fade, progress } from '../lib/anim';
import { useCues } from '../lib/useStory';
import { RouteCard } from './parts/RouteCard';
import type { SceneProps } from './types';
import './scenes.css';

const T_STAMP = 1.0;
const T_FLY = 2.6;
const FLY_DUR = 2.5;

/** Back on the map: London is done, the line runs on and Coco heads for Oxford. */
export function S8Journey({ t, active, reduced }: SceneProps) {
  const vp = useViewport();
  const wide = vp.width >= 900;
  const pad: Padding = wide
    ? { top: 110, right: 76, bottom: 96, left: Math.min(380, vp.width * 0.3) }
    : { top: 120, right: 58, bottom: 100, left: 14 };
  const cams = useMemo(() => {
    const view = { width: vp.width, height: vp.height };
    return {
      london: frameCamera([STOP_POINTS.london, STOP_POINTS.oxford], view, pad, 140, 3.4),
      ahead: frameCamera(Object.values(STOP_POINTS), view, pad, 70, 3),
    };
  }, [vp.width, vp.height, pad.left, pad.top, pad.right, pad.bottom]); // eslint-disable-line react-hooks/exhaustive-deps

  const path = useMemo(() => Array.from({ length: 31 }, (_, i) => ROUTE.at(STOP_AT.london + ((STOP_AT.oxford - STOP_AT.london) * i) / 30)), []);
  const plan = useMemo(() => new FlightPlan([{ start: T_FLY, duration: FLY_DUR, path, land: 'stand', ease: 'inOut' }], { at: STOP_POINTS.london }), [path]);
  const fl = plan.at(reduced ? 99 : t);
  const travelled = reduced ? STOP_AT.oxford : STOP_AT.london + (STOP_AT.oxford - STOP_AT.london) * ease.inOut(clamp(progress(t, T_FLY - 0.3, FLY_DUR) * 1.1));
  const camera = reduced ? cams.ahead : cameraAt(t, [[0, cams.london], [T_FLY + FLY_DUR + 0.2, cams.london], [T_FLY + FLY_DUR + 2.6, cams.ahead]]);
  const stamp = reduced ? 1 : ease.outBack(progress(t, T_STAMP, 0.5));

  useCues(t, [[T_STAMP, () => sound.play('stamp')], [T_FLY - 0.25, () => sound.play('flap')], [T_FLY - 0.3, () => sound.play('pen', { duration: FLY_DUR, volume: 0.6 })], [T_FLY + FLY_DUR - 0.1, () => sound.play('chirp')]], active);

  return (
    <div className="s8">
      <UkMap
        route={travelled}
        routePlanned={1}
        completed={t >= T_STAMP || reduced ? ['london'] : []}
        current={t >= T_FLY - 0.3 ? 'oxford' : 'london'}
        camera={camera}
        interactive={active}
        coco={{ at: fl, mode: fl.mode, facing: fl.facing, tilt: fl.tilt, cue: t > T_FLY + FLY_DUR + 0.6 ? { kind: 'excite', id: 1 } : null }}
        reduced={reduced}
        padding={pad}
        overlay={(toScreen) => {
          const p = toScreen(STOP_POINTS.london);
          return t >= T_STAMP || reduced ? (
            <div className="stamp" style={{ left: p.x, top: p.y, transform: `translate(-50%, 34px) rotate(-8deg) scale(${stamp})`, opacity: clamp(stamp) * fade(t, 0, 0.01, 7.5, 1) }}>
              <span>London</span>
              <b>Complete</b>
            </div>
          ) : null;
        }}
      />
      {wide && <RouteCard t={t} appear={1} reached={t >= T_FLY + FLY_DUR - 0.3 ? ['london', 'oxford'] : ['london']} completed={t >= T_STAMP ? ['london'] : []} current={t >= T_FLY - 0.3 ? 'oxford' : 'london'} title="Next stop: Oxford" />}
    </div>
  );
}
