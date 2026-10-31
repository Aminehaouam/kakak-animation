import { memo } from 'react';
import { rng } from '../../lib/anim';
import type { CityPalette } from '../palette';
import { Band } from '../shadow';
import { BigBen, LondonEye, Parliament } from './Landmarks';
import { Bus, Cloud, Lamp, Person, PhoneBox, Railing, Taxi, Tree } from './Street';

export const STREET_W = 1600;
export const STREET_H = 900;
const RIVER = [548, 640] as const;
const ROAD = [690, 792] as const;

/** Where things stand in the street view. */
export const STREET = {
  bigBen: { x: 470, y: 640 },
  phoneBox: { x: 1180, y: 872 },
  /** the top of the phone box's dome (the curve peaks at -114 in box units), where Coco perches */
  phoneTop: { x: 1180, y: 872 - 114 * 2.2 + 3 },
};

const Backdrop = memo(function Backdrop({ pal }: { pal: CityPalette }) {
  const flags = rng(5);
  return (
    <g>
      <defs>
        <linearGradient id="street-sky" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor={pal.sky[0]} />
          <stop offset="0.6" stopColor={pal.sky[1]} />
          <stop offset="1" stopColor={pal.sky[2]} />
        </linearGradient>
        <linearGradient id="street-river" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor={pal.water[0]} />
          <stop offset="1" stopColor={pal.water[2]} />
        </linearGradient>
      </defs>
      <rect width={STREET_W} height={RIVER[1]} fill="url(#street-sky)" />
      <circle cx={1420} cy={130} r={180} fill={pal.sunGlow} />
      <circle cx={1420} cy={130} r={46} fill={pal.sun} />
      {/* South Bank across the river */}
      {Array.from({ length: 12 }).map((_, i) => {
        const h = 50 + flags() * 90;
        return <rect key={i} x={640 + i * 82} y={RIVER[0] - h} width={76} height={h} fill={i % 2 ? pal.hazeFar : pal.haze} />;
      })}
      <rect x={600} y={RIVER[0]} width={1000} height={RIVER[1] - RIVER[0]} fill="url(#street-river)" />
      {Array.from({ length: 16 }).map((_, i) => (
        <rect key={i} x={620 + flags() * 950} y={RIVER[0] + 10 + flags() * 70} width={30 + flags() * 80} height={2.4} rx={1.2} fill={pal.waterLine} opacity={0.6} />
      ))}
      {/* Parliament and the clock tower on our side */}
      <g transform={`translate(-150 ${RIVER[1]}) scale(1.25)`}>
        <Parliament pal={pal} width={470} />
      </g>
      <g transform={`translate(${STREET.bigBen.x} ${STREET.bigBen.y}) scale(1.45)`}>
        <BigBen pal={pal} minutes={10 * 60 + 12} />
      </g>
      <g transform={`translate(${STREET_W} ${RIVER[1]}) scale(-1 1)`}>
        <Railing pal={pal} width={1000} />
      </g>
      <rect x={560} y={RIVER[1]} width={1040} height={10} fill={pal.wallTop} />
      <rect x={0} y={RIVER[1] + 8} width={STREET_W} height={ROAD[0] - RIVER[1] - 8} fill={pal.pavement} />
      <Band x={0} y={RIVER[1] + 8} w={STREET_W} h={14} color={pal.shadow} />
      <rect x={0} y={ROAD[0] - 8} width={STREET_W} height={8} fill={pal.wallTop} />
      <rect x={0} y={ROAD[0]} width={STREET_W} height={ROAD[1] - ROAD[0]} fill={pal.road} />
      {Array.from({ length: 12 }).map((_, i) => (
        <rect key={i} x={20 + i * 140} y={(ROAD[0] + ROAD[1]) / 2 - 3} width={80} height={6} rx={3} fill={pal.roadLine} />
      ))}
      <rect x={0} y={ROAD[1]} width={STREET_W} height={10} fill={pal.wallTop} />
      <rect x={0} y={ROAD[1] + 10} width={STREET_W} height={STREET_H - ROAD[1]} fill={pal.pavement} />
      <Band x={0} y={ROAD[1] + 10} w={STREET_W} h={10} color={pal.shadow} strength={0.8} />
      {Array.from({ length: 24 }).map((_, i) => (
        <line key={i} x1={i * 70} y1={ROAD[1] + 10} x2={i * 70 - 40} y2={STREET_H} stroke={pal.wall} strokeWidth={2} opacity={0.4} />
      ))}
      {[836, 872].map((y) => (
        <line key={y} x1={0} y1={y} x2={STREET_W} y2={y} stroke={pal.wall} strokeWidth={2} opacity={0.35} />
      ))}
    </g>
  );
});

/** `perch` (0..1): Coco sits on the phone box, so its dome takes his shadow. */
export const LondonStreet = memo(function LondonStreet({ pal, t, still = false, perch = 0 }: { pal: CityPalette; t: number; still?: boolean; perch?: number }) {
  const time = still ? 4 : t;
  const busX = -420 + (time - 0.3) * 330;
  const taxiX = STREET_W + 260 - (time - 1.4) * 380;
  return (
    <svg viewBox={`0 0 ${STREET_W} ${STREET_H}`} preserveAspectRatio="xMidYMid slice" aria-hidden>
      <Backdrop pal={pal} />
      {[{ x: 260, y: 110, s: 2, w: 260 }, { x: 900, y: 70, s: 6, w: 200 }].map((c, i) => (
        <g key={i} transform={`translate(${c.x + time * (6 + i * 3)} ${c.y})`}>
          <Cloud pal={pal} seed={c.s} w={c.w} />
        </g>
      ))}
      <g transform={`translate(1230 ${RIVER[0]}) scale(0.72)`}>
        <LondonEye pal={pal} angle={time * 1.6} />
      </g>
      {[640, 760, 1500].map((x, i) => (
        <g key={x} transform={`translate(${x} ${RIVER[1] + 30})`}>
          <Tree pal={pal} size={1.1} seed={i + 40} />
        </g>
      ))}
      <g transform={`translate(${taxiX} ${ROAD[0] + 44}) scale(-1.9 1.9)`}>
        <Taxi pal={pal} />
      </g>
      <g transform={`translate(${busX} ${ROAD[1] - 4}) scale(1.95)`}>
        <Bus pal={pal} route="11" dest="Westminster" />
      </g>
      <g transform={`translate(920 ${STREET.phoneBox.y})`}>
        <g transform="scale(2.2)">
          <Lamp pal={pal} />
        </g>
      </g>
      <g transform={`translate(${STREET.phoneBox.x} ${STREET.phoneBox.y}) scale(2.2)`}>
        <PhoneBox pal={pal} perch={perch} />
      </g>
      {Array.from({ length: 5 }).map((_, i) => {
        const r = rng(i + 70);
        const dir = r() < 0.5 ? -1 : 1;
        const speed = 40 + r() * 30;
        const x = ((((r() * 1900 + dir * time * speed) % 1900) + 1900) % 1900) - 150;
        return (
          <g key={i} transform={`translate(${x} ${846 + r() * 40}) scale(${dir * 2.6} 2.6)`}>
            <Person seed={i + 20} phase={time * speed * 0.1 + i} shade={pal.shadow} />
          </g>
        );
      })}
    </svg>
  );
});
