import { useMemo } from 'react';
import { sound } from '../audio/sound';
import { DAY } from '../art/palette';
import { LondonStreet, STREET, STREET_H, STREET_W } from '../art/london/StreetScene';
import { CocoActor } from '../components/coco/CocoActor';
import { FlightPlan } from '../components/coco/flight';
import { cameraAt, frameCamera } from '../components/map/camera';
import { STOP_POINTS } from '../components/map/geo';
import { UkMap } from '../components/map/UkMap';
import { Stage, useViewport } from '../components/stage/Stage';
import { ease, keys, progress } from '../lib/anim';
import { useCues } from '../lib/useStory';
import type { SceneProps } from './types';
import './scenes.css';

const IRIS = [1.7, 1.2] as const; // start, duration

/** The map dives into London and opens onto the street by Big Ben. */
export function S5London({ t, active, reduced }: SceneProps) {
  const vp = useViewport();
  const none = { top: 0, right: 0, bottom: 0, left: 0 };
  const cams = useMemo(() => {
    const view = { width: vp.width, height: vp.height };
    const all = frameCamera(Object.values(STOP_POINTS), view, vp.width >= 900 ? { top: 96, right: 76, bottom: 96, left: Math.min(380, vp.width * 0.3) } : { top: 70, right: 58, bottom: 100, left: 14 }, 70, 3);
    return { all, london: { ...STOP_POINTS.london, zoom: 8 } };
  }, [vp.width, vp.height]);
  // dive onto London; the last plunge while the street opens is a GPU scale of the map layer,
  // so the rasters aren't redrawn at huge zooms
  const mapCam = cameraAt(t, [[0, cams.all], [IRIS[0] + 0.2, cams.london, 'inOut']]);
  const plunge = reduced ? 1 : 1 + 1.1 * ease.in(progress(t, IRIS[0] + 0.2, IRIS[1]));

  // the street: on a phone the camera walks from Big Ben to the phone box
  const camX = vp.portrait ? keys(t, [[2.2, 520], [5.6, STREET.phoneBox.x + 20]]) : 820;
  const zoom = reduced ? 1 : 1 + 0.05 * ease.out(progress(t, 2, 7));
  const plan = useMemo(() => {
    const from = { x: vp.portrait ? 1500 : 1700, y: 120 };
    return new FlightPlan(
      [{ start: 3.1, duration: 2.1, path: [from, { x: 1350, y: 330 }, { x: STREET.phoneTop.x + 60, y: STREET.phoneTop.y - 80 }, STREET.phoneTop], land: 'perch', ease: 'out' }],
      { at: from, mode: 'fly', facing: 'left' },
    );
  }, [vp.portrait]);
  const fl = reduced ? { ...STREET.phoneTop, mode: 'perch' as const, facing: 'left' as const, tilt: 0, scale: 1 } : plan.at(t);
  // Coco's shadow on the dome, as he settles on it
  const onBox = reduced ? 1 : ease.inOut(progress(t, 4.95, 0.3));

  const r = reduced ? (t > IRIS[0] ? 1 : 0) : ease.inOut(progress(t, IRIS[0], IRIS[1]));
  const radius = r * Math.hypot(vp.width, vp.height) * 0.62;
  useCues(t, [[IRIS[0], () => sound.play('whoosh')], [2.6, () => sound.play('bell', { volume: 0.45 })], [2.9, () => sound.play('flap')], [5.1, () => sound.play('chirp')]], active);

  return (
    <div className="s5">
      {r < 1 && (
        <div className="s5__map" style={{ transform: plunge > 1 ? `scale(${plunge})` : undefined }}>
          <UkMap route={1} camera={reduced ? cams.london : mapCam} reduced={reduced} padding={none} />
        </div>
      )}
      <div
        className="s5__street"
        style={r < 1 ? { clipPath: `circle(${radius}px at 50% 50%)`, WebkitClipPath: `circle(${radius}px at 50% 50%)` } : undefined}
      >
        <Stage width={STREET_W} height={STREET_H} camera={{ x: camX, y: STREET_H / 2 + 20, zoom }}>
          <LondonStreet pal={DAY} t={t} still={reduced} perch={onBox} />
          {(t >= 2.9 || reduced) && <CocoActor state={fl} height={150} cue={t > 6.4 ? { kind: 'look', id: 1 } : null} still={reduced} label="Coco on a red telephone box" />}
        </Stage>
      </div>
      {r > 0 && r < 1 && <div className="s5__ring" style={{ width: radius * 2, height: radius * 2 }} />}
    </div>
  );
}
