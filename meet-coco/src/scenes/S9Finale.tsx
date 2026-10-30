import { useLayoutEffect, useMemo, useRef, useState, type RefObject } from 'react';
import { sound } from '../audio/sound';
import { SUNSET } from '../art/palette';
import { LondonPanorama, PANO_H, PANO_W } from '../art/london/Panorama';
import { CocoActor } from '../components/coco/CocoActor';
import { FlightPlan } from '../components/coco/flight';
import { Stage, useViewport } from '../components/stage/Stage';
import { APP } from '../config/app';
import { FINALE } from '../config/story';
import { fade, tween } from '../lib/anim';
import { useCues } from '../lib/useStory';
import type { SceneProps } from './types';
import './scenes.css';

/** "MEET COCO" with the last letter of each word wrapped, so Coco knows where to perch. */
function splitTitle(title: string, first: RefObject<HTMLSpanElement | null>, last: RefObject<HTMLSpanElement | null>) {
  const words = title.split(' ');
  return words.map((w, i) => (
    <span key={i} className="finale__word">
      {w.slice(0, -1)}
      <span ref={i === 0 ? first : i === words.length - 1 ? last : undefined}>{w.slice(-1)}</span>
      {i < words.length - 1 ? ' ' : ''}
    </span>
  ));
}

export function S9Finale({ t, active, reduced, onGo }: SceneProps) {
  const vp = useViewport();
  const titleRef = useRef<HTMLHeadingElement>(null);
  const tRef = useRef<HTMLSpanElement>(null);
  const oRef = useRef<HTMLSpanElement>(null);
  const [perch, setPerch] = useState<{ x: number; y: number } | null>(null);
  useLayoutEffect(() => {
    const el = titleRef.current!;
    // Coco perches on the top right letter: the last O on one line, the T when "MEET COCO" wraps
    // measured from layout offsets, so the title's rise-in animation doesn't skew the spot
    const measure = () => {
      const fs = parseFloat(getComputedStyle(el).fontSize);
      const wrapped = el.offsetHeight > fs * 1.4;
      const letter = (wrapped ? tRef.current : oRef.current)!;
      const box = (letter.offsetParent as HTMLElement).getBoundingClientRect();
      setPerch({
        x: box.left + letter.offsetLeft + letter.offsetWidth * 0.5,
        y: box.top + letter.offsetTop + (letter.offsetHeight - fs) / 2 + fs * 0.31,
      });
    };
    measure();
    const ro = new ResizeObserver(measure);
    ro.observe(el);
    document.fonts?.ready.then(measure);
    return () => ro.disconnect();
  }, []);

  const narrow = vp.width < 760;
  const cocoH = narrow ? 104 : Math.min(150, vp.height * 0.18);
  const target = perch ?? { x: vp.width * 0.7, y: vp.height * 0.4 };
  const plan = useMemo(
    () =>
      new FlightPlan(
        [{ start: 2.6, duration: 2.4, path: [{ x: vp.width + 160, y: vp.height * 0.12 }, { x: vp.width * 0.82, y: target.y - vp.height * 0.2 }, target], land: 'perch', ease: 'out' }],
        { at: { x: vp.width + 160, y: vp.height * 0.12 }, mode: 'fly', facing: 'left' },
      ),
    [vp.width, vp.height, target.x, target.y],
  );
  const fl = reduced ? { ...target, mode: 'perch' as const, facing: 'left' as const, tilt: 0, scale: 1 } : plan.at(t);
  const cue = t > 5.8 ? { kind: 'excite' as const, id: 1 } : null;

  useCues(t, [[0.4, () => sound.play('bell', { volume: 0.5 })], [2.4, () => sound.play('flap')], [4.9, () => sound.play('chirp')], [5.9, () => sound.play('squawk', { volume: 0.6 })]], active);

  const camX = narrow ? 980 : 1240;
  const zoom = reduced ? 1 : tween(t, 0, 9, 1, 1.06, 'out');
  const start = () => {
    sound.play('ding');
    if (APP.startUrl) window.location.assign(APP.startUrl);
    else onGo?.(3, 19);
  };

  return (
    <div className="s9">
      <Stage width={PANO_W} height={PANO_H} camera={{ x: camX, y: 700, zoom }}>
        <LondonPanorama pal={SUNSET} t={t + 120} camX={camX} still={reduced} clock={19 * 60 + 42} />
      </Stage>
      <div className="s9__glow" />
      <div className="finale">
        <h1 ref={titleRef} className="finale__title" style={{ opacity: fade(t, 0.8, 1.2), transform: `translateY(${reduced ? 0 : tween(t, 0.8, 1.6, 18, 0, 'out')}px)` }}>
          {splitTitle(FINALE.title, tRef, oRef)}
        </h1>
        <p className="finale__subtitle" style={{ opacity: fade(t, 1.8, 1.0) }}>
          {FINALE.subtitle}
        </p>
        <button className="finale__cta" style={{ opacity: fade(t, 5.4, 0.8), pointerEvents: t > 5.4 ? 'auto' : 'none' }} onClick={start} tabIndex={t > 5.4 ? 0 : -1}>
          {FINALE.button}
          <svg viewBox="0 0 24 24" width="20" height="20" aria-hidden>
            <path d="M5 12h12m-5-6 6 6-6 6" stroke="currentColor" strokeWidth="2.4" fill="none" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </button>
      </div>
      {(t >= 2.2 || reduced) && (
        <div className="finale__coco">
          <CocoActor state={fl} height={cocoH} cue={cue} still={reduced} label="Coco, perched beside the title" />
        </div>
      )}
    </div>
  );
}
