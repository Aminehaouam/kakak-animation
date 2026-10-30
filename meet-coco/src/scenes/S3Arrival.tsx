import { useMemo } from 'react';
import { sound } from '../audio/sound';
import { DAY } from '../art/palette';
import { LondonPanorama, PANO, PANO_H, PANO_W } from '../art/london/Panorama';
import { CocoActor } from '../components/coco/CocoActor';
import { FlightPlan } from '../components/coco/flight';
import { Stage, useViewport } from '../components/stage/Stage';
import { ease, progress } from '../lib/anim';
import { useCues } from '../lib/useStory';
import type { SceneProps } from './types';
import './scenes.css';

const CAM_Y = 790;

export function S3Arrival({ t, active, reduced }: SceneProps) {
  const vp = useViewport();
  const zoom = vp.portrait ? 1 : 1.3;
  const cover = Math.max(vp.width / PANO_W, vp.height / PANO_H) * zoom;
  const halfW = vp.width / cover / 2;
  // the camera drifts from Big Ben toward the City; on a phone it settles where Coco lands
  const pan = (time: number) => 860 + 1140 * ease.inOut(progress(time, 0, 10));
  const land = PANO.lampNear(vp.portrait ? 1400 : pan(4.6) + halfW * 0.3);
  const camAt = (time: number) =>
    reduced ? (vp.portrait ? land.x : 1350) : vp.portrait ? 860 + (land.x + 20 - 860) * ease.inOut(progress(time, 0, 5.2)) : pan(time);

  const plan = useMemo(() => {
    const from = { x: camAt(2.0) - halfW - 120, y: 260 };
    return new FlightPlan(
      [{ start: 2.0, duration: 2.6, path: [from, { x: (from.x + land.x) / 2, y: 470 }, { x: land.x - 70, y: land.y - 90 }, land], land: 'perch', ease: 'out' }],
      { at: from, mode: 'fly' },
    );
  }, [halfW, land.x, reduced]); // eslint-disable-line react-hooks/exhaustive-deps

  const fl = reduced ? { ...land, mode: 'perch' as const, facing: 'right' as const, tilt: 0, scale: 1 } : plan.at(t);
  useCues(t, [[1.8, () => sound.play('flap')], [4.5, () => sound.play('chirp')], [6.3, () => sound.play('chirp', { volume: 0.5 })]], active);

  return (
    <div className="s3 tiltshift">
      <Stage width={PANO_W} height={PANO_H} camera={{ x: camAt(t), y: CAM_Y, zoom }}>
        <LondonPanorama pal={DAY} t={t + 30} camX={camAt(t)} still={reduced} />
        {(t >= 1.6 || reduced) && (
          <CocoActor state={fl} height={170} cue={t >= 6.2 ? { kind: 'look', id: 1 } : null} still={reduced} label="Coco the parrot" />
        )}
      </Stage>
    </div>
  );
}
