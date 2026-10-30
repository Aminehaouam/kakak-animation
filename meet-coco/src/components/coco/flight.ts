import { clamp, ease, type Ease } from '../../lib/anim';
import { smooth, Track, type Pt } from '../../lib/path';
import { COCO_DURATIONS, type CocoMode } from './Coco';

/** One flight: Coco takes off at the first waypoint and travels the smoothed path. */
export interface Leg {
  /** When the motion along the path starts (s). Coco crouches and jumps just before. */
  start: number;
  duration: number;
  path: Pt[];
  ease?: Ease;
  /** How Coco lands at the end; omit to keep flying (a following leg continues). */
  land?: Exclude<CocoMode, 'fly'>;
  /** Size multiplier at the start and end of the leg (perspective). */
  scale?: [number, number];
}

export interface FlightState extends Pt {
  mode: CocoMode;
  facing: 'left' | 'right';
  /** degrees, a gentle bank into climbs and dives */
  tilt: number;
  scale: number;
}

// The Rive animations: the body leaves the ground ~0.28 s into "takeoff"; "land" touches down
// at 0.33 s, so the landing pose starts a little before the path ends.
const TAKEOFF_LEAD = Math.min(0.28, COCO_DURATIONS.takeoff);
const LAND_LEAD = 0.3;

export class FlightPlan {
  private legs: Array<Leg & { track: Track }>;
  private rest: { at: Pt; mode: CocoMode; facing: 'left' | 'right'; scale: number };

  constructor(
    legs: Leg[],
    rest: { at: Pt; mode?: CocoMode; facing?: 'left' | 'right'; scale?: number },
  ) {
    this.legs = legs.map((l) => ({ ...l, track: new Track(smooth(l.path, 24)) }));
    this.rest = { at: rest.at, mode: rest.mode ?? 'stand', facing: rest.facing ?? 'right', scale: rest.scale ?? 1 };
  }

  /** Where Coco is at t if every flight that has begun had already landed (reduced motion). */
  settled(t: number): FlightState {
    const begun = this.legs.filter((l) => t >= l.start - TAKEOFF_LEAD);
    const last = begun[begun.length - 1];
    if (!last) return this.at(-Infinity);
    const end = this.at(last.start + last.duration);
    return { ...end, mode: last.land ?? end.mode, tilt: 0 };
  }

  at(t: number): FlightState {
    let state: FlightState = { ...this.rest.at, mode: this.rest.mode, facing: this.rest.facing, tilt: 0, scale: this.rest.scale };
    for (const leg of this.legs) {
      const [s0, s1] = leg.scale ?? [state.scale, state.scale];
      if (t < leg.start - TAKEOFF_LEAD) break;
      const start = leg.track.at(0);
      if (t < leg.start) {
        // anticipation: the takeoff animation crouches on the spot
        state = { ...state, x: start.x, y: start.y, mode: 'fly', scale: s0 };
        break;
      }
      const u = clamp((t - leg.start) / leg.duration);
      const e = ease[leg.ease ?? 'inOut'](u);
      const p = leg.track.at(e);
      const ahead = leg.track.at(Math.min(e + 0.01, 1));
      const behind = leg.track.at(Math.max(e - 0.01, 0));
      const dx = ahead.x - behind.x;
      const dy = ahead.y - behind.y;
      const overall = leg.track.at(1).x - start.x;
      const facing = Math.abs(dx) > 0.15 * Math.hypot(dx, dy) ? (dx < 0 ? 'left' : 'right') : overall < 0 ? 'left' : 'right';
      const slope = Math.atan2(dy, Math.abs(dx) || 1e-6) * (180 / Math.PI);
      const settle = 1 - ease.inOut(clamp((t - (leg.start + leg.duration - 0.45)) / 0.45));
      const landing = leg.land && t >= leg.start + leg.duration - LAND_LEAD;
      state = {
        x: p.x,
        y: p.y,
        mode: u >= 1 ? leg.land ?? 'fly' : landing ? leg.land! : 'fly',
        facing,
        tilt: Math.max(-14, Math.min(14, slope * 0.35)) * settle * (facing === 'left' ? -1 : 1),
        scale: s0 + (s1 - s0) * e,
      };
      if (u < 1) break;
      state.tilt = 0;
    }
    return state;
  }
}
