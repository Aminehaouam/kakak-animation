// Street furniture, vehicles and people. Each piece stands on (0, 0) and faces right.
import { memo } from 'react';
import { rng } from '../../lib/anim';
import type { CityPalette } from '../palette';
import { Contact } from '../shadow';

type P = { pal: CityPalette };

/** A red double-decker: 150 long, 104 tall. */
export const Bus = memo(function Bus({ pal, route = '11', dest = 'Westminster' }: P & { route?: string; dest?: string }) {
  const glass = pal.name === 'sunset' ? '#ffcf9a' : '#cee7f3';
  return (
    <g>
      <Contact cx={75} cy={4} rx={84} ry={6} color={pal.shadow} />
      <path d="M0 -8 V-92 Q0 -104 12 -104 H136 Q150 -104 150 -90 V-8 Z" fill={pal.red} />
      <rect x={0} y={-58} width={150} height={6} fill={pal.redShade} />
      <rect x={0} y={-14} width={150} height={6} fill={pal.redShade} />
      {Array.from({ length: 6 }).map((_, i) => (
        <rect key={i} x={10 + i * 20} y={-96} width={16} height={24} rx={3} fill={glass} />
      ))}
      {Array.from({ length: 4 }).map((_, i) => (
        <rect key={i} x={10 + i * 22} y={-50} width={18} height={24} rx={3} fill={glass} />
      ))}
      <rect x={104} y={-50} width={20} height={42} rx={2} fill={pal.redShade} />
      <rect x={106} y={-48} width={7} height={36} rx={1.5} fill={glass} opacity={0.85} />
      <rect x={115} y={-48} width={7} height={36} rx={1.5} fill={glass} opacity={0.85} />
      <path d="M133 -96 H146 V-72 H133Z" fill={glass} />
      <rect x={130} y={-50} width={16} height={26} rx={3} fill={glass} />
      <rect x={128} y={-102} width={20} height={6} rx={2} fill="#16181d" />
      <text x={138} y={-97.6} fontSize={4.2} fill="#ffd34d" textAnchor="middle" fontWeight={700} fontFamily="var(--font-ui)">
        {route} {dest}
      </text>
      <rect x={146} y={-20} width={4} height={6} rx={1} fill="#fff6c8" />
      {[30, 118].map((x) => (
        <g key={x}>
          <circle cx={x} cy={-6} r={11} fill={pal.black} />
          <circle cx={x} cy={-6} r={5} fill="#9aa0a8" />
        </g>
      ))}
    </g>
  );
});

/** A black cab: 104 long, 52 tall; the roof sign glows when for hire. */
export const Taxi = memo(function Taxi({ pal, forHire = true, shadow = true }: P & { forHire?: boolean; shadow?: boolean }) {
  const glass = pal.name === 'sunset' ? '#fbbf89' : pal.name === 'rain' ? '#9db3c6' : '#b9dae8';
  return (
    <g>
      {shadow && <Contact cx={53} cy={1} rx={58} ry={5} color={pal.shadow} />}
      <path d="M2 -10 Q0 -26 8 -28 L22 -30 Q30 -50 42 -52 H74 Q86 -51 92 -32 L100 -30 Q106 -26 104 -10Z" fill={pal.black} />
      <path d="M36 -31 Q44 -47 50 -47 H58 V-31Z" fill={glass} />
      <path d="M62 -47 H72 Q82 -46 86 -31 H62Z" fill={glass} />
      <rect x={54} y={-56} width={14} height={5} rx={1.5} fill={forHire ? '#ffd86b' : '#505050'} />
      <text x={61} y={-52.3} fontSize={3.6} textAnchor="middle" fontWeight={800} fill="#1d1f24" fontFamily="var(--font-ui)">
        TAXI
      </text>
      <rect x={6} y={-22} width={94} height={2} fill="#fff" opacity={0.18} />
      <rect x={100} y={-22} width={4} height={5} rx={1} fill="#fff6c8" />
      <rect x={0} y={-20} width={3} height={5} rx={1} fill="#ee2e23" />
      {[22, 84].map((x) => (
        <g key={x}>
          <circle cx={x} cy={-8} r={9} fill="#0d0e11" />
          <circle cx={x} cy={-8} r={4} fill="#a6abb3" />
        </g>
      ))}
    </g>
  );
});

/** The red telephone box: 40 wide, 118 tall; `perch` (0..1) shades the dome under Coco's feet. */
export const PhoneBox = memo(function PhoneBox({ pal, glow = 0, perch = 0 }: P & { glow?: number; perch?: number }) {
  const glass = pal.name === 'sunset' ? '#ffd9a6' : '#d9ecf2';
  return (
    <g>
      <Contact cx={3} cy={0} rx={30} ry={4.5} color={pal.shadow} />
      <rect x={-22} y={-6} width={44} height={6} fill={pal.redShade} />
      <rect x={-20} y={-104} width={40} height={98} fill={pal.red} />
      <path d="M-22 -104 Q0 -124 22 -104Z" fill={pal.red} />
      <path d="M-14 -110 Q0 -120 14 -110" fill="none" stroke={pal.redShade} strokeWidth={2} />
      {perch > 0 && (
        <g>
          <clipPath id="phonebox-dome">
            <path d="M-22 -104 Q0 -124 22 -104Z" />
          </clipPath>
          <g clipPath="url(#phonebox-dome)">
            <Contact cx={1.5} cy={-112.5} rx={13} ry={3} color={pal.shadow} strength={1.4 * perch} />
          </g>
        </g>
      )}
      <rect x={-17} y={-102} width={34} height={8} fill="#f6f1e6" />
      <text x={0} y={-96} fontSize={5} textAnchor="middle" fontWeight={800} letterSpacing={0.6} fill={pal.ink} fontFamily="var(--font-ui)">
        TELEPHONE
      </text>
      <rect x={-15} y={-90} width={30} height={76} fill={glass} opacity={0.9} />
      {glow > 0 && <rect x={-15} y={-90} width={30} height={76} fill="#ffe2a0" opacity={glow} />}
      {[1, 2].map((i) => (
        <rect key={i} x={-15 + i * 10 - 0.8} y={-90} width={1.6} height={76} fill={pal.red} />
      ))}
      {Array.from({ length: 7 }).map((_, i) => (
        <rect key={i} x={-15} y={-90 + (i + 1) * 9.5} width={30} height={1.6} fill={pal.red} />
      ))}
      <rect x={-20} y={-104} width={6} height={98} fill={pal.redShade} opacity={0.35} />
    </g>
  );
});

/** A Victorian street lamp: 120 tall; `on` lights it. */
export const Lamp = memo(function Lamp({ pal, on = 0 }: P & { on?: number }) {
  return (
    <g>
      <Contact cx={2} cy={0} rx={13} ry={3} color={pal.shadow} />
      {on > 0 && <circle cx={0} cy={-108} r={34} fill={pal.windowLit} opacity={0.22 * on} />}
      <rect x={-6} y={-12} width={12} height={12} rx={2} fill={pal.black} />
      <rect x={-2.5} y={-96} width={5} height={86} fill={pal.black} />
      <path d="M-9 -96 H9 L6 -100 H-6Z" fill={pal.black} />
      <path d="M-8 -100 L-10 -118 H10 L8 -100Z" fill={on > 0 ? pal.windowLit : '#f3ecd8'} opacity={on > 0 ? 0.6 + 0.4 * on : 0.85} />
      <path d="M-12 -118 H12 L0 -127Z" fill={pal.black} />
      <circle cx={0} cy={-129} r={2} fill={pal.black} />
    </g>
  );
});

/** A London plane tree: canopy about 90 wide. */
export const Tree = memo(function Tree({ pal, size = 1, seed = 1 }: P & { size?: number; seed?: number }) {
  const r = rng(seed);
  const blobs = Array.from({ length: 6 }, (_, i) => ({ x: (r() - 0.5) * 60, y: -70 - r() * 40, r: 22 + r() * 14, c: i % 3 }));
  return (
    <g transform={`scale(${size})`}>
      <Contact cx={5} cy={0} rx={28} ry={5.5} color={pal.shadow} strength={0.85} />
      <path d="M-4 0 L-3 -64 L-14 -84 M-3 -64 L10 -88 M0 -40 L3 -64" stroke={pal.trunk} strokeWidth={7} strokeLinecap="round" fill="none" />
      {blobs.map((b, i) => (
        <circle key={i} cx={b.x} cy={b.y} r={b.r} fill={pal.tree[b.c]} />
      ))}
      <circle cx={-14} cy={-104} r={14} fill={pal.tree[0]} opacity={0.8} />
    </g>
  );
});

const SKIN = ['#f3c6a3', '#daa179', '#aa6e49', '#7c4a31', '#eab78f'];
const CLOTHES = ['#155892', '#da331f', '#f4b738', '#1f7e53', '#704498', '#e8e2d4', '#24282f', '#ea6e37'];

/** A small person walking; `phase` swings the legs, `umbrella` for the rain; `shade` colours the
 * shadow at their feet. */
export const Person = memo(function Person({ seed, phase = 0, umbrella = false, size = 1, shade = '#1f2a44' }: { seed: number; phase?: number; umbrella?: boolean; size?: number; shade?: string }) {
  const r = rng(seed * 7919 + 13);
  const skin = SKIN[Math.floor(r() * SKIN.length)];
  const top = CLOTHES[Math.floor(r() * CLOTHES.length)];
  const legs = ['#24282f', '#35496a', '#564435'][Math.floor(r() * 3)];
  const swing = Math.sin(phase) * 3.4;
  const bob = Math.abs(Math.cos(phase)) * 0.8;
  const hair = ['#23160f', '#5a3112', '#d1963c', '#8c8c8c'][Math.floor(r() * 4)];
  return (
    <g transform={`scale(${size})`}>
      <Contact cx={0.6} cy={0.2} rx={7} ry={1.7} color={shade} />
      <g transform={`translate(0 ${-bob})`}>
        <path d={`M-1.5 -12 L${-1.5 - swing} 0 M1.5 -12 L${1.5 + swing} 0`} stroke={legs} strokeWidth={3} strokeLinecap="round" />
        <rect x={-4.5} y={-25} width={9} height={14} rx={4} fill={top} />
        <circle cx={0} cy={-29.5} r={4.3} fill={skin} />
        <path d="M-4.3 -30 a4.3 4.3 0 0 1 8.6 0 q-4 -2 -8.6 0z" fill={hair} />
        {umbrella && (
          <g>
            <line x1={3} y1={-22} x2={3} y2={-40} stroke="#2c2c2c" strokeWidth={1} />
            <path d="M-10 -38 Q3 -52 16 -38Z" fill={top === '#24282f' ? '#da331f' : '#24282f'} />
          </g>
        )}
      </g>
    </g>
  );
});

/** A Thames river boat: 170 long. */
export const Boat = memo(function Boat({ pal }: P) {
  return (
    <g>
      <Contact cx={86} cy={5} rx={82} ry={4.5} color={pal.shadow} strength={0.8} />
      <path d="M0 -14 H170 L158 4 H10Z" fill="#f5f2ea" />
      <path d="M4 -4 H166 L158 4 H10Z" fill={pal.ink} opacity={0.75} />
      <rect x={30} y={-36} width={112} height={22} rx={6} fill="#f5f2ea" />
      {Array.from({ length: 8 }).map((_, i) => (
        <rect key={i} x={36 + i * 13} y={-32} width={9} height={11} rx={2} fill={pal.glass} />
      ))}
      <rect x={44} y={-40} width={84} height={4} rx={2} fill={pal.red} />
      <line x1={150} y1={-14} x2={150} y2={-46} stroke={pal.ink} strokeWidth={1.5} />
      <path d="M150 -46 h12 l-3 4 l3 4 h-12z" fill={pal.red} />
    </g>
  );
});

/** A stone balustrade `width` long, 26 tall. */
export const Railing = memo(function Railing({ pal, width }: P & { width: number }) {
  const n = Math.floor(width / 14);
  return (
    <g>
      <rect x={0} y={-26} width={width} height={6} rx={2} fill={pal.wallTop} />
      {Array.from({ length: n }).map((_, i) => (
        <path key={i} d={`M${7 + i * 14 - 3} -20 q-2 6 0 10 q-2 5 1 10 h4 q3 -5 1 -10 q2 -4 0 -10z`} fill={pal.wallTop} opacity={0.9} />
      ))}
      <rect x={0} y={-2} width={width} height={4} fill={pal.wall} />
    </g>
  );
});

/** A pigeon in flight, 14 wide; `flap` 0..1 moves the wings. */
export const Pigeon = memo(function Pigeon({ flap = 0, color = '#5c636d' }: { flap?: number; color?: string }) {
  const w = Math.sin(flap * Math.PI * 2) * 5;
  return <path d={`M-8 ${-w} Q-3 -2 0 0 Q3 -2 8 ${-w}`} stroke={color} strokeWidth={1.8} fill="none" strokeLinecap="round" />;
});

export interface Building {
  x: number;
  w: number;
  h: number;
  color: string;
  roof: 'flat' | 'gable' | 'mansard';
  cols: number;
  rows: number;
  lit: boolean[];
  chimneys: number;
}

/** A row of terraced buildings from x0 to x1 (deterministic for a seed). */
export function terrace(seed: number, x0: number, x1: number, pal: CityPalette, minH = 90, maxH = 170): Building[] {
  const r = rng(seed);
  const out: Building[] = [];
  let x = x0;
  while (x < x1) {
    const w = 60 + Math.floor(r() * 4) * 18;
    const h = minH + r() * (maxH - minH);
    const cols = Math.max(2, Math.floor(w / 22));
    const rows = Math.max(2, Math.floor((h - 20) / 30));
    out.push({
      x,
      w,
      h,
      color: pal.brick[Math.floor(r() * pal.brick.length)],
      roof: (['flat', 'gable', 'mansard'] as const)[Math.floor(r() * 3)],
      cols,
      rows,
      lit: Array.from({ length: cols * rows }, () => r() < pal.lit),
      chimneys: Math.floor(r() * 3),
    });
    x += w + (r() < 0.3 ? 4 : 0);
  }
  return out;
}

export const Terrace = memo(function Terrace({ buildings, pal }: { buildings: Building[]; pal: CityPalette }) {
  return (
    <g>
      {buildings.map((b, i) => (
        <g key={i} transform={`translate(${b.x} 0)`}>
          <rect x={0} y={-b.h} width={b.w} height={b.h} fill={b.color} />
          <rect x={b.w - 10} y={-b.h} width={10} height={b.h} fill="#000" opacity={0.12} />
          <rect x={0} y={-16} width={b.w} height={16} fill={pal.shadow} opacity={0.07} />
          {b.roof === 'gable' && <path d={`M-3 ${-b.h} L${b.w / 2} ${-b.h - 30} L${b.w + 3} ${-b.h}Z`} fill={pal.roof} />}
          {b.roof === 'mansard' && <path d={`M-2 ${-b.h} L8 ${-b.h - 22} H${b.w - 8} L${b.w + 2} ${-b.h}Z`} fill={pal.roof} />}
          {b.roof === 'flat' && <rect x={-2} y={-b.h - 5} width={b.w + 4} height={6} fill={pal.wallTop} opacity={0.8} />}
          {Array.from({ length: b.chimneys }).map((_, c) => (
            <rect key={c} x={10 + c * (b.w - 28)} y={-b.h - (b.roof === 'flat' ? 20 : 34)} width={8} height={16} fill={pal.brick[4]} />
          ))}
          {Array.from({ length: b.rows }).map((_, ry) =>
            Array.from({ length: b.cols }).map((_, cx) => {
              const gw = b.w / b.cols;
              return (
                <rect
                  key={`${ry}-${cx}`}
                  x={cx * gw + gw * 0.28}
                  y={-b.h + 16 + ry * 30}
                  width={gw * 0.44}
                  height={17}
                  rx={1.5}
                  fill={b.lit[ry * b.cols + cx] ? pal.windowLit : pal.window}
                  opacity={b.lit[ry * b.cols + cx] ? 0.95 : 0.7}
                />
              );
            }),
          )}
        </g>
      ))}
    </g>
  );
});

/** A soft cumulus cloud about 220 wide. */
export const Cloud = memo(function Cloud({ pal, seed = 1, w = 220 }: P & { seed?: number; w?: number }) {
  const r = rng(seed);
  const k = w / 220;
  const blobs = Array.from({ length: 6 }, (_, i) => ({ x: (-90 + i * 36 + r() * 12) * k, y: (-r() * 34 - (i === 2 || i === 3 ? 22 : 0)) * k, r: (24 + r() * 22 + (i === 2 || i === 3 ? 12 : 0)) * k }));
  return (
    <g>
      {blobs.map((b, i) => (
        <circle key={`s${i}`} cx={b.x + 4 * k} cy={b.y + 7 * k} r={b.r} fill={pal.cloudShade} />
      ))}
      {blobs.map((b, i) => (
        <circle key={i} cx={b.x} cy={b.y} r={b.r} fill={pal.cloud} />
      ))}
      <rect x={-110 * k} y={-6 * k} width={220 * k} height={14 * k} rx={7 * k} fill={pal.cloud} />
    </g>
  );
});
