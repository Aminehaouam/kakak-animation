import { memo, useMemo } from 'react';
import { rng } from '../../lib/anim';
import type { CityPalette } from '../palette';
import { Band } from '../shadow';
import { BigBen, Gherkin, LondonEye, Parliament, Shard, StPauls, TowerBridge } from './Landmarks';
import { Boat, Bus, Cloud, Lamp, Person, Pigeon, Railing, Taxi, Terrace, Tree, terrace } from './Street';

export const PANO_W = 3200;
export const PANO_H = 1200;
const BANK = 820; // the far bank, where the landmarks stand
const WALL = 1000; // top of the near embankment
const ROAD = [1046, 1122] as const;

/** Where things are in the panorama, for placing Coco and the camera. */
export const PANO = {
  bigBen: { x: 900, y: BANK - 400 },
  eye: { x: 1500, y: BANK - 234 },
  towerBridge: { x: 2760, y: BANK - 200 },
  railing: (x: number) => ({ x, y: WALL - 26 }),
  /** the top of the street lamp nearest to x (Coco's favourite perch) */
  lampNear: (x: number) => ({ x: 140 + Math.round((x - 140) / 260) * 260, y: WALL - 129 }),
  bank: BANK,
  wall: WALL,
};

interface PanoramaProps {
  pal: CityPalette;
  /** seconds, for traffic, boats, clouds and the wheel */
  t: number;
  /** camera centre x in panorama units (for parallax) */
  camX: number;
  /** pause all the little motions (reduced motion) */
  still?: boolean;
  /** time on Big Ben, minutes after midnight */
  clock?: number;
}

const SkyLayer = memo(function SkyLayer({ pal }: { pal: CityPalette }) {
  const sunX = pal.name === 'sunset' ? 2050 : 2500;
  const sunY = pal.name === 'sunset' ? 700 : 190;
  return (
    <g>
      <defs>
        <linearGradient id={`sky-${pal.name}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor={pal.sky[0]} />
          <stop offset="0.55" stopColor={pal.sky[1]} />
          <stop offset="0.82" stopColor={pal.sky[2]} />
        </linearGradient>
        <radialGradient id={`sun-${pal.name}`}>
          <stop offset="0" stopColor={pal.sun} />
          <stop offset="0.18" stopColor={pal.sun} />
          <stop offset="0.35" stopColor={pal.sunGlow} />
          <stop offset="1" stopColor={pal.sunGlow} stopOpacity={0} />
        </radialGradient>
      </defs>
      <rect x={-400} y={0} width={PANO_W + 800} height={BANK + 40} fill={`url(#sky-${pal.name})`} />
      <circle cx={sunX} cy={sunY} r={pal.name === 'sunset' ? 420 : 300} fill={`url(#sun-${pal.name})`} />
    </g>
  );
});

const FarLayer = memo(function FarLayer({ pal }: { pal: CityPalette }) {
  const towers = useMemo(() => {
    const r = rng(42);
    return Array.from({ length: 70 }, (_, i) => ({ x: -300 + i * 54 + r() * 30, w: 30 + r() * 50, h: 60 + r() * (i > 34 && i < 50 ? 230 : 120), top: r() }));
  }, []);
  return (
    <g>
      {towers.map((b, i) => (
        <g key={i}>
          <rect x={b.x} y={BANK - 60 - b.h} width={b.w} height={b.h + 60} fill={i % 2 ? pal.hazeFar : pal.haze} />
          {b.top > 0.8 && <rect x={b.x + b.w / 2 - 1} y={BANK - 60 - b.h - 26} width={2} height={26} fill={pal.haze} />}
        </g>
      ))}
      {/* a crane or two: London is always building */}
      <g fill="none" stroke={pal.haze} strokeWidth={4}>
        <path d={`M1180 ${BANK - 60} V${BANK - 330} M1100 ${BANK - 320} H1330 M1180 ${BANK - 330} L1300 ${BANK - 320}`} />
        <path d={`M2380 ${BANK - 60} V${BANK - 360} M2300 ${BANK - 350} H2520`} />
      </g>
    </g>
  );
});

const MidLayer = memo(function MidLayer({ pal, clock }: { pal: CityPalette; clock: number }) {
  const left = useMemo(() => terrace(7, -320, 150, pal, 110, 190), [pal]);
  const mid = useMemo(() => terrace(11, 1000, 1290, pal, 80, 150), [pal]);
  const city = useMemo(() => terrace(19, 1700, 2440, pal, 120, 230), [pal]);
  const right = useMemo(() => terrace(23, 3020, 3560, pal, 100, 190), [pal]);
  return (
    <g>
      <g transform={`translate(0 ${BANK})`}>
        <Terrace buildings={left} pal={pal} />
        <Terrace buildings={city} pal={pal} />
        <Terrace buildings={right} pal={pal} />
        <Terrace buildings={mid} pal={pal} />
      </g>
      <g transform={`translate(1900 ${BANK - 40})`}>
        <StPauls pal={pal} />
      </g>
      <g transform={`translate(2140 ${BANK})`}>
        <Gherkin pal={pal} />
      </g>
      <g transform={`translate(2300 ${BANK})`}>
        <Shard pal={pal} />
      </g>
      <g transform={`translate(150 ${BANK})`}>
        <Parliament pal={pal} width={700} />
      </g>
      <g transform={`translate(900 ${BANK})`}>
        <BigBen pal={pal} minutes={clock} />
      </g>
      {[1010, 1120, 1250, 1330, 1640].map((x, i) => (
        <g key={x} transform={`translate(${x} ${BANK})`}>
          <Tree pal={pal} size={0.75} seed={i + 3} />
        </g>
      ))}
      <rect x={-400} y={BANK - 4} width={PANO_W + 800} height={10} fill={pal.wall} />
    </g>
  );
});

const NearStatic = memo(function NearStatic({ pal }: { pal: CityPalette }) {
  return (
    <g>
      <rect x={-400} y={WALL} width={PANO_W + 800} height={PANO_H - WALL + 40} fill={pal.pavement} />
      <rect x={-400} y={ROAD[0]} width={PANO_W + 800} height={ROAD[1] - ROAD[0]} fill={pal.road} />
      {Array.from({ length: 44 }).map((_, i) => (
        <rect key={i} x={-380 + i * 90} y={(ROAD[0] + ROAD[1]) / 2 - 2} width={46} height={4} rx={2} fill={pal.roadLine} opacity={0.8} />
      ))}
      <rect x={-400} y={ROAD[1]} width={PANO_W + 800} height={6} fill={pal.wallTop} />
      <rect x={-400} y={ROAD[0] - 6} width={PANO_W + 800} height={6} fill={pal.wallTop} />
      {/* soft shade under the embankment wall and the far kerb */}
      <Band x={-400} y={WALL + 2} w={PANO_W + 800} h={14} color={pal.shadow} />
      <Band x={-400} y={ROAD[1] + 6} w={PANO_W + 800} h={8} color={pal.shadow} strength={0.8} />
      <g transform={`translate(-400 ${WALL})`}>
        <Railing pal={pal} width={PANO_W + 800} />
      </g>
    </g>
  );
});

export const LondonPanorama = memo(function LondonPanorama({ pal, t, camX, still = false, clock = 10 * 60 + 9 }: PanoramaProps) {
  const time = still ? 0 : t;
  const par = (depth: number) => (camX - PANO_W / 2) * (1 - depth);
  const eyeAngle = time * 1.6;
  const dusk = pal.name === 'sunset' ? 1 : 0;
  // traffic: buses and cabs loop along the road in both directions
  const traffic = [
    { kind: 'bus', speed: 120, offset: 0, lane: 1, dir: 1 },
    { kind: 'taxi', speed: 170, offset: 900, lane: 1, dir: 1 },
    { kind: 'taxi', speed: 150, offset: 2200, lane: 0, dir: -1 },
    { kind: 'bus', speed: 105, offset: 1500, lane: 0, dir: -1 },
    { kind: 'taxi', speed: 160, offset: 2900, lane: 1, dir: 1 },
  ];
  const span = PANO_W + 600;
  const people = Array.from({ length: 26 }, (_, i) => i);
  return (
    <svg viewBox={`0 0 ${PANO_W} ${PANO_H}`} preserveAspectRatio="xMidYMid slice" aria-hidden>
      <SkyLayer pal={pal} />
      {[
        { x: 300, y: 170, w: 260, s: 3, v: 6 },
        { x: 1250, y: 120, w: 200, s: 5, v: 4 },
        { x: 2250, y: 210, w: 300, s: 9, v: 7 },
        { x: 3000, y: 140, w: 180, s: 12, v: 5 },
      ].map((c, i) => (
        <g key={i} transform={`translate(${((c.x + time * c.v + par(0.15) + 400) % (PANO_W + 800)) - 400} ${c.y})`} opacity={0.92}>
          <Cloud pal={pal} seed={c.s} w={c.w} />
        </g>
      ))}
      <g transform={`translate(${par(0.35)} 0)`}>
        <FarLayer pal={pal} />
      </g>
      <g transform={`translate(${par(0.7)} 0)`}>
        <g id={`midbank-${pal.name}`}>
          <MidLayer pal={pal} clock={clock} />
        </g>
        <g transform={`translate(1500 ${BANK})`}>
          <LondonEye pal={pal} angle={eyeAngle} />
        </g>
        <g transform={`translate(2500 ${BANK})`}>
          <TowerBridge pal={pal} />
        </g>
        {/* pigeons over the river */}
        {[0, 1, 2, 3].map((i) => (
          <g key={i} transform={`translate(${(600 + i * 70 + time * 40) % 3400} ${330 + i * 18 + Math.sin(time + i) * 8})`}>
            <Pigeon flap={time * 2.2 + i * 0.3} color={dusk ? '#33283a' : '#525c67'} />
          </g>
        ))}
      </g>
      {/* the Thames */}
      <g transform={`translate(${par(0.85)} 0)`}>
        <defs>
          <linearGradient id={`river-${pal.name}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor={pal.water[0]} />
            <stop offset="0.45" stopColor={pal.water[1]} />
            <stop offset="1" stopColor={pal.water[2]} />
          </linearGradient>
        </defs>
        <rect x={-500} y={BANK + 6} width={PANO_W + 1000} height={WALL - BANK} fill={`url(#river-${pal.name})`} />
        {/* the far bank's shade on the water */}
        <Band x={-500} y={BANK + 6} w={PANO_W + 1000} h={16} color={pal.shadow} />
        <clipPath id={`riverclip-${pal.name}`}>
          <rect x={-500} y={BANK + 6} width={PANO_W + 1000} height={WALL - BANK} />
        </clipPath>
        {/* the far bank mirrored in the water */}
        <g clipPath={`url(#riverclip-${pal.name})`} opacity={dusk ? 0.22 : 0.16}>
          <use href={`#midbank-${pal.name}`} transform={`translate(${par(0.7) - par(0.85)} ${2 * BANK + 8}) scale(1 -1)`} />
        </g>
        {dusk > 0 &&
          Array.from({ length: 12 }).map((_, i) => {
            const w = 30 + (12 - i) * 16 + Math.sin(time * 1.3 + i) * 10;
            return <rect key={i} x={2050 - w / 2 + Math.sin(i * 2.1) * 30} y={BANK + 14 + i * 13} width={w} height={3.2} rx={1.6} fill={pal.sun} opacity={0.55 - i * 0.03} />;
          })}
        {Array.from({ length: 34 }).map((_, i) => {
          const r = rng(i + 100);
          const y = BANK + 18 + r() * (WALL - BANK - 30);
          const w = 30 + r() * 110;
          const x = ((r() * (PANO_W + 800) + time * (10 + r() * 14)) % (PANO_W + 800)) - 400;
          return <rect key={i} x={x} y={y} width={w} height={2.4} rx={1.2} fill={pal.waterLine} opacity={0.35 + 0.4 * Math.abs(Math.sin(time * 0.8 + i))} />;
        })}
        {[0, 1].map((i) => {
          const dir = i ? -1 : 1;
          const x = i ? 2600 - ((time * 34) % 3600) : ((time * 28 + 400) % 3600) - 300;
          return (
            <g key={i} transform={`translate(${x} ${BANK + 70 + i * 52}) scale(${dir * (0.9 + i * 0.15)} ${0.9 + i * 0.15})`}>
              <Boat pal={pal} />
            </g>
          );
        })}
      </g>
      {/* the near embankment and road */}
      <g transform={`translate(${par(1)} 0)`}>
        <NearStatic pal={pal} />
        {Array.from({ length: 14 }).map((_, i) => (
          <g key={i} transform={`translate(${140 + i * 260} ${WALL})`}>
            <Lamp pal={pal} on={dusk} />
          </g>
        ))}
        {Array.from({ length: 8 }).map((_, i) => (
          <g key={i} transform={`translate(${270 + i * 470} ${WALL + 30})`}>
            <Tree pal={pal} size={0.8} seed={i + 30} />
          </g>
        ))}
        {traffic.map((v, i) => {
          const p = (v.offset + time * v.speed) % span;
          const x = v.dir > 0 ? p - 300 : PANO_W + 300 - p;
          const y = v.lane ? ROAD[1] - 6 : ROAD[0] + 26;
          return (
            <g key={i} transform={`translate(${x} ${y}) scale(${v.dir} 1)`}>
              {v.kind === 'bus' ? <Bus pal={pal} route={['11', '24', '88'][i % 3]} /> : <Taxi pal={pal} />}
            </g>
          );
        })}
        {people.map((i) => {
          const r = rng(i + 500);
          const dir = r() < 0.5 ? -1 : 1;
          const speed = 18 + r() * 16;
          const row = r() < 0.5 ? WALL + 30 : ROAD[1] + 50 + r() * 20;
          const x = (((r() * (PANO_W + 400) + dir * time * speed) % (PANO_W + 400)) + PANO_W + 400) % (PANO_W + 400) - 200;
          return (
            <g key={i} transform={`translate(${x} ${row}) scale(${dir * 1.15} 1.15)`}>
              <Person seed={i} phase={time * speed * 0.32 + i} shade={pal.shadow} />
            </g>
          );
        })}
      </g>
    </svg>
  );
});
