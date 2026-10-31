import { memo } from 'react';
import { Coco, COCO_FEET, type CocoCue } from './Coco';
import type { FlightState } from './flight';

interface CocoActorProps {
  state: FlightState;
  /** Height of Coco's box in the parent's units (px of the stage). */
  height: number;
  cue?: CocoCue;
  still?: boolean;
  silhouette?: number;
  opacity?: number;
  label?: string;
  className?: string;
  /** 0..1: a soft contact shadow at the feet while Coco stands or perches on a flat surface. */
  shadow?: number;
}

/** Coco placed by the feet at (state.x, state.y) in the parent's coordinates. */
export const CocoActor = memo(function CocoActor({ state, height, cue, still, silhouette, opacity = 1, label, className, shadow = 0 }: CocoActorProps) {
  const h = height * state.scale;
  const coco = (
    <div
      className={className}
      style={{
        position: 'absolute',
        left: 0,
        top: 0,
        width: h * 0.9,
        height: h,
        opacity,
        transform: `translate(${state.x - h * 0.9 * COCO_FEET.x}px, ${state.y - h * COCO_FEET.y}px) rotate(${state.tilt}deg)`,
        transformOrigin: `${COCO_FEET.x * 100}% ${COCO_FEET.y * 70}%`,
        pointerEvents: 'none',
      }}
    >
      <Coco mode={state.mode} facing={state.facing} cue={cue} still={still} silhouette={silhouette} label={label} style={{ height: '100%' }} />
    </div>
  );
  if (shadow <= 0) return coco;
  // grounded only (it fades out on takeoff and back in on landing); an ink drawing casts none
  const strength = state.mode === 'fly' ? 0 : shadow * (1 - Math.min(Math.max(silhouette ?? 0, 0), 1)) * opacity;
  const w = h * 0.42;
  return (
    <>
      <i className="coco-shadow" aria-hidden style={{ width: w, height: w * 0.16, opacity: strength, transform: `translate(${state.x - w / 2 + h * 0.03}px, ${state.y - w * 0.07}px)` }} />
      {coco}
    </>
  );
});
