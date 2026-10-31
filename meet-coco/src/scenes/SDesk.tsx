import { useMemo } from 'react';
import { sound } from '../audio/sound';
import { Desk, DESK, DESK_H, DESK_W, JOURNAL, TICKET } from '../art/Desk';
import { CocoActor } from '../components/coco/CocoActor';
import { FlightPlan } from '../components/coco/flight';
import { cameraAt } from '../components/map/camera';
import { Stage, useViewport } from '../components/stage/Stage';
import { clamp, ease, keys, progress } from '../lib/anim';
import { useCues } from '../lib/useStory';
import type { SceneProps } from './types';
import './scenes.css';

// Scenes 1 and 2 share one desk and one timeline: scene 2 starts where scene 1 ends.
const PART2 = 8.5;
const T_OPEN = 1.6;
const T_INK = 5.0;
const T_ALIVE = PART2 + 0.7;
const T_TAKEOFF = PART2 + 2.0;
const FLIGHT = 3.3;

function DeskScene({ time, active, reduced }: { time: number; active: boolean; reduced: boolean }) {
  const vp = useViewport();
  const T = reduced ? 99 : time; // reduced motion: the journal is simply open
  const open = reduced ? 1 : ease.inOut(progress(T, T_OPEN, 1.5));
  const band = ease.in(progress(T, T_OPEN - 0.6, 0.5));
  const writing = progress(T, T_OPEN + 1.4, 2.4);
  const ink = reduced ? 1 : ease.out(progress(T, T_INK, 1.4));
  const alive = reduced ? (time >= PART2 ? 1 : 0) : ease.inOut(progress(time, T_ALIVE, 0.9));

  // Coco: drawn on the page, comes alive, loops over the desk and lands on LONDON
  const plan = useMemo(() => {
    const p = DESK.page;
    const k = DESK.ticket;
    return new FlightPlan(
      [
        {
          start: T_TAKEOFF,
          duration: FLIGHT,
          // up off the page, a loop around the journal, then down onto LONDON
          path: [p, { x: p.x + 150, y: p.y - 320 }, { x: 860, y: 140 }, { x: 470, y: 230 }, { x: 400, y: 560 }, { x: 640, y: 830 }, { x: 1040, y: 860 }, { x: k.x - 40, y: k.y - 130 }, k],
          land: 'perch',
          ease: 'inOut',
          scale: [1, 0.95],
        },
      ],
      { at: p, mode: 'stand' },
    );
  }, []);
  const fl = reduced ? (time >= PART2 ? { ...DESK.ticket, mode: 'perch' as const, facing: 'left' as const, tilt: 0, scale: 0.95 } : { ...DESK.page, mode: 'stand' as const, facing: 'right' as const, tilt: 0, scale: 1 }) : plan.at(time);
  const flying = time > T_TAKEOFF - 0.2 && time < T_TAKEOFF + FLIGHT + 0.2;
  const height = keys(time, [[T_TAKEOFF, 0], [T_TAKEOFF + 0.4, 1], [T_TAKEOFF + FLIGHT - 0.5, 1], [T_TAKEOFF + FLIGHT, 0]]);

  const wide = !vp.portrait;
  const journal = { x: JOURNAL.x, y: JOURNAL.y + JOURNAL.h / 2 };
  const ticket = { x: TICKET.x + TICKET.w / 2, y: TICKET.y + TICKET.h / 2 - 30 };
  const flightCam = (zoom: number) => {
    const c = plan.at(time - 0.18); // a little behind Coco, so the camera eases after him
    return { x: c.x, y: c.y - 110, zoom };
  };
  let camera;
  if (reduced) camera = time < PART2 ? { x: journal.x, y: 520, zoom: 1.1 } : { ...ticket, zoom: 1.25 };
  else if (wide)
    camera = cameraAt(time, [
      [0, { x: 800, y: 500, zoom: 1 }],
      [T_INK + 1.2, { x: journal.x + 60, y: 500, zoom: 1.2 }],
      [PART2 + 1.6, { x: journal.x + 60, y: 500, zoom: 1.2 }],
      [T_TAKEOFF + FLIGHT * 0.45, { x: 800, y: 500, zoom: 1 }],
      [T_TAKEOFF + FLIGHT + 1.0, { ...ticket, zoom: 1.35 }],
    ]);
  else {
    // a phone sees one page at a time: the cover, the notes, the drawing, then Coco's flight
    const right = { x: JOURNAL.x + JOURNAL.w * 0.52, y: 480, zoom: 1 };
    const left = { x: JOURNAL.x - JOURNAL.w * 0.5, y: 480, zoom: 1 };
    const scripted = cameraAt(time, [
      [0, { x: JOURNAL.x + JOURNAL.w / 2, y: 470, zoom: 1 }],
      [T_OPEN + 0.4, { x: JOURNAL.x + JOURNAL.w / 2, y: 470, zoom: 1 }],
      [T_OPEN + 1.6, left],
      [T_INK - 0.3, left],
      [T_INK + 0.6, right],
      [T_TAKEOFF, right],
    ]);
    const follow = keys(time, [[T_TAKEOFF - 0.1, 0], [T_TAKEOFF + 0.5, 1]]);
    const f = flightCam(1);
    const land = keys(time, [[T_TAKEOFF + FLIGHT - 0.4, 0], [T_TAKEOFF + FLIGHT + 0.8, 1]]);
    const end = { ...ticket, zoom: 1.12 };
    const mid = { x: scripted.x + (f.x - scripted.x) * follow, y: scripted.y + (f.y - scripted.y) * follow, zoom: 1 };
    camera = { x: mid.x + (end.x - mid.x) * land, y: mid.y + (end.y - mid.y) * land, zoom: 1 + (end.zoom - 1) * land };
  }

  useCues(
    time,
    [
      [T_OPEN - 0.4, () => sound.play('tick', { volume: 0.8 })],
      [T_OPEN, () => sound.play('page')],
      [T_OPEN + 1.4, () => sound.play('pen', { duration: 2.2, volume: 0.5 })],
      [T_INK, () => sound.play('whoosh', { volume: 0.3 })],
      [T_ALIVE + 0.3, () => sound.play('chirp')],
      [T_TAKEOFF - 0.25, () => sound.play('flap')],
      [T_TAKEOFF + FLIGHT - 0.1, () => sound.play('chirp')],
      [T_TAKEOFF + FLIGHT + 0.9, () => sound.play('squawk', { volume: 0.5 })],
    ],
    active,
  );

  const showCoco = ink > 0.01;
  const cocoH = 300;
  return (
    <Stage width={DESK_W} height={DESK_H} camera={camera}>
      <Desk open={open} writing={writing} band={band} t={reduced ? 0 : time} />
      {showCoco && flying && (
        // a soft shadow on the desk sells the height
        <div
          className="desk-shadow"
          style={{ left: fl.x + 70 * height, top: fl.y + 46 * height, width: 150 - 40 * height, height: 34 - 10 * height, opacity: 0.35 - 0.18 * height }}
        />
      )}
      {showCoco && (
        <div style={{ position: 'absolute', inset: 0, opacity: clamp(ink * 1.2), clipPath: alive > 0 ? undefined : `circle(${ink * 62}% at ${(DESK.page.x / DESK_W) * 100}% ${((DESK.page.y - 120) / DESK_H) * 100}%)` }}>
          <CocoActor
            state={fl}
            height={cocoH}
            shadow={1}
            silhouette={1 - alive}
            cue={time > T_TAKEOFF + FLIGHT + 0.8 ? { kind: 'excite', id: 1 } : null}
            still={reduced || alive < 0.5}
            label={alive > 0.5 ? 'Coco the parrot' : undefined}
          />
        </div>
      )}
    </Stage>
  );
}

export function S1Journal(props: SceneProps) {
  return <DeskScene time={props.t} active={props.active} reduced={props.reduced} />;
}

export function S2Meet(props: SceneProps) {
  return <DeskScene time={PART2 + props.t} active={props.active} reduced={props.reduced} />;
}
